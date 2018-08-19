#!/usr/bin/python
import json
import time
import re
from queue import Queue
import os
import requests
import MySQLdb
from bs4 import BeautifulSoup

"""
login
log
timer
"""


class spider(object):
    def __init__(self):
        """
        初始化
        """
        self.bookmark_url = "https://www.pixiv.net/bookmark.php?rest=show&p=1"
        self.login_api = "https://accounts.pixiv.net/api/login?lang=zh"
        self.login_url = "https://accounts.pixiv.net/login"
        self.session = requests.session()
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 "
                          "Safari/536.3 "
        }
        self.pixiv_id = ""
        self.password = ""
        self.url_dict_queue = Queue()
        self.date = time.strftime("%Y%b", time.localtime())
        self.page_num = 1
        self.total_pic_num = 0
        self.conn = None
        self.picid_list = []

    def get_postkey(self):
        """
        获取登录页面的postkey
        :return:
        """
        resp = self.session.get(self.login_url, headers=self.headers)
        matchObj = re.search('"pixivAccount.postKey":"(\w*?)"', resp.text, re.S)  # 正则匹配postkey
        return matchObj.group(1)

    def login(self):
        """
        构建headers和formData，把headers和formData用post的方式发送到pixiv的登录api
        :return: 返回是否登录成功的布尔值
        """
        headers = self.headers
        post_key = self.get_postkey()
        headers.update({
            "dnt": "1",
            "origin": "https://accounts.pixiv.net",
            "referer": "https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index"})
        form_data = {
            "post_key": post_key,
            "pixiv_id": self.pixiv_id,
            "password": self.password,
            "ref": "wwwtop_accounts_index",
            "return_to": "https: // www.pixiv.net /"
        }
        resp = self.session.post(self.login_api, data=form_data, headers=headers)
        resp_dict = resp.json()  # 返回字典
        if "success" in resp_dict["body"]:
            print("登录成功")
            return True
        else:
            print("登录失败,请检查账号密码")
            return False

    def get_urls(self):
        """
        以get的方式获取收藏页面
        用beautifulSoup获取图片链接
        将获取的图片id，原始url，图片页面url存进字典队列中
        :return:
        """
        picid_new_list = []
        resp = self.session.get(self.bookmark_url)
        soup = BeautifulSoup(resp.text, "html.parser")
        result_set = soup.find_all("a", attrs={"class": re.compile("work _work")})  # 抓取图片浏览页面url

        for tag in result_set:
            num = 0
            referer_url = "https://www.pixiv.net/" + tag.get("href")
            pic_id = re.search("id=(\d*)", referer_url, re.S).group(1)  # 正则匹配图片id
            if int(pic_id) not in self.picid_list:
                url = tag.img.get("data-src")
                if tag.span is not None:
                    num = int(tag.span.string)  # 取得图片的张数
                picid_new_list.append(pic_id)
                original_url = url.replace("c/150x150/img-master", "img-original").replace("_master1200", "")
                # 构建图片原始url
                url_dict = {  # url字典，用于构建request
                    "num": num,
                    "pic_id": pic_id,
                    "original_url": original_url,
                    "referer_url": referer_url
                }
                self.url_dict_queue.put(url_dict)
                self.total_pic_num += 1  # 计数器，计算一共多少张图
        if self.has_next_page(soup):  # 如果有下一页，就进行迭代
            self.page_num += 1
            self.bookmark_url = re.sub("(?<=show&p=)\d+", str(self.page_num), self.bookmark_url)
            self.get_urls()
        else:
            print(self.total_pic_num)
        for pic_id in picid_new_list:
            self.write_database(pic_id)

    def download(self):
        """
        取出url字典并进行下载
        :return:
        """
        while not self.url_dict_queue.empty():

            try:
                url_dict = self.url_dict_queue.get()
                referer_url = url_dict["referer_url"]
                original_url = url_dict["original_url"]
                pic_id = url_dict["pic_id"]
                num = url_dict["num"]
                if url_dict["num"] != 0:
                    print("id=" + url_dict["pic_id"] + "有多张图片\n")
                    for i in range(0, num):
                        num = str(i)
                        print(referer_url)
                        original_url = re.sub("\d+(?=.jpg)", num, original_url)
                        print(original_url)
                        self.download_single_pic(referer_url, original_url, pic_id + "_p" + num)
                else:
                    self.download_single_pic(referer_url, original_url, pic_id)
            except Exception as e:
                print(e)

    def download_single_pic(self, referer_url, original_url, pic_id):
        """
        下载单张图片
        对png和jpg进行判断
        :param referer_url: 图片预览页面url
        :param original_url: 图片原始页面url
        :param pic_id: 图片id
        :return:
        """
        try:
            headers = {
                "user-agent": "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 "
                              "Safari/536.3",
                "Referer": referer_url,
            }
            resp = self.session.get(original_url,
                                    headers=headers)
            if resp.status_code != 200:
                new_img_url = original_url.replace(".jpg", ".png")
                resp = self.session.get(new_img_url, headers=headers)
                if resp.status_code != 200:
                    print("发生错误，图片id=" + pic_id + "\n")
                    print(resp.status_code)
                else:
                    print("成功获取下载id=" + pic_id + "图片\n")
                    with open(self.date + "/" + pic_id + ".png", "wb") as f:
                        f.write(resp.content)
            else:
                print("成功获取id=" + pic_id + "图片\n")
                with open(self.date + "/" + pic_id + ".jpg", "wb") as f:
                    f.write(resp.content)
        except Exception as e:
            print(e)

    def makdir_by_date(self):
        """
        按月份创建文件夹，不能创建成功就把图片下载到主程序所在文件夹里
        :return:
        """
        try:
            if not os.path.exists(self.date):
                os.makedirs(self.date)
                print("创建名为\"" + self.date + "\"的文件夹\n")
            else:
                print("已经存在名为\"" + self.date + "\"的文件夹\n")
        except Exception as e:
            print(e)
            self.date = ""

    def has_next_page(self, soup):
        """
        判断是否有下一页
        :param soup: 分析图片预览页面的soup对象
        :return: 返回有无下一页的布尔值
        """
        result_set = soup.find_all("a", attrs={"rel": "next"})
        if len(result_set) == 0:
            return False
        else:
            return True

    def write_database(self, pic_id):
        cursor = self.conn.cursor()
        sql = "insert into pic_info values (" + pic_id + ");"
        try:
            cursor.execute(sql)
            self.conn.commit()
            cursor.close()
        except Exception as e:
            print(e)

    def read_database(self):
        cursor = self.conn.cursor()
        sql = "select*from pic_info"
        try:
            cursor.execute(sql)
            results = cursor.fetchall()
            self.conn.commit()
            cursor.close()
            for result in results:
                self.picid_list.append(result[0])
        except Exception as e:
            print(e)

    def get_connection(self):
        try:
            self.conn = MySQLdb.connect(host="localhost", port=3306, user="", passwd="",
                                        db="pixiv_spider",
                                        charset='utf8')
            return True
        except Exception as e:
            print(e)

    def close_connection(self):
        try:
            self.conn.close()
        except Exception as e:
            print(e)

    def check_login(self):
        resp = self.session.get("https://www.pixiv.net/bookmark.php?rest=show&p=1")
        print(resp.json())


if __name__ == '__main__':
    spider = spider()
    if spider.get_connection():
        spider.login()
        spider.read_database()
        spider.get_urls()
        spider.makdir_by_date()
        spider.download()
        spider.close_connection()
