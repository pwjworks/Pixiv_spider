import re
from queue import Queue

import requests
from bs4 import BeautifulSoup


class spider(object):
    def __init__(self):
        self.bookmark_url = "https://www.pixiv.net/bookmark.php"
        self.login_api = "https://accounts.pixiv.net/api/login?lang=zh"
        self.login_url = "https://accounts.pixiv.net/login"
        self.session = requests.session()
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3"
        }
        self.pixiv_id = ""
        self.password = ""
        self.original_url = Queue()
        self.num=1

    def get_PostId(self):
        resp = self.session.get(self.login_url, headers=self.headers)
        matchObj = re.search('"pixivAccount.postKey":"(\w*?)"', resp.text, re.S)
        return matchObj.group(1)

    def login(self):
        headers = self.headers
        post_key = self.get_PostId()
        headers.update({
            "dnt": "1",
            "origin": "https://accounts.pixiv.net",
            "referer": "https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index"})
        formData = {
            "post_key": post_key,
            "pixiv_id": self.pixiv_id,
            "password": self.password,
            "ref": "wwwtop_accounts_index",
            "return_to": "https: // www.pixiv.net /"
        }
        resp = self.session.post(self.login_api, data=formData, headers=headers)

    def check_login(self):
        resp = self.session.get(self.login_url, headers=self.headers)
        print(resp.text)

    def get_urls(self):
        resp = self.session.get(self.bookmark_url)
        soup = BeautifulSoup(resp.text, "html.parser")
        resultSet = soup.find_all("a", attrs={"class": "work _work "})

        for tag in resultSet:
            url = tag.img.get("data-src")
            original_url = url.replace("c/150x150/img-master", "img-original").replace("_master1200", "")
            self.original_url.put(original_url)
            print(original_url)

    def download(self):
        # while not self.original_url.empty():
            try:
                img_url=self.original_url.get()
                resp= self.session.get("https://i.pximg.net/img-original/img/2018/06/15/01/19/53/69210112_p0.png")
                if resp.status_code==403:
                    new_img_url=img_url.replace(".jpg",".png")



                # with open(str(self.num)+".png","wb") as f:
                #     f.write(resp.content)
                # print(resp.content)
            except Exception as e:
                print(e)


if __name__ == '__main__':
    spider=spider()
    spider.login()
    # spider.get_urls()
    spider.download()
