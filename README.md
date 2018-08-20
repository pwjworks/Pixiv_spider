**简介**
======

基于requests,mysql,cookiejar，实现下载插画交流网站pixiv“收藏”图片





简述爬虫思路
======


**1.模拟登录pixiv**


登录页面：


![登录页面](https://github.com/pwjworks/Pixiv_spider/blob/master/img_folder/login_page.PNG)

模拟登录pixiv需要获得藏在登录页面报文中的postkey(仅本次访问有效)，我们必须把postkey提取出来，把它写入我们post请求的报文里
（对比其他网站，pivix真是单纯不做作啊(￣▽￣)"）

![postkey](https://github.com/pwjworks/Pixiv_spider/blob/master/img_folder/post_key.PNG)

我们可以根据pixiv返回的json报文判断是否登录成功

失败案例：
![fail](https://github.com/pwjworks/Pixiv_spider/blob/master/img_folder/json1.PNG)

成功案例：
![success](https://github.com/pwjworks/Pixiv_spider/blob/master/img_folder/json2.PNG)

登录成功后，使用cookiejar保存cookies文件以便下次使用

**2.获取原图url**

使用chrome的F12工具并进入收藏页面,jian我们可以发现页面中的图img的class都是"work _work"

![bookmark](https://github.com/pwjworks/Pixiv_spider/blob/master/img_folder/bookmark_page.PNG)
点击图片，可以发现并不是原图，是"midium"图片
![mid](https://github.com/pwjworks/Pixiv_spider/blob/master/img_folder/mid_url2.PNG)

打开大图，就可以发现原图链接，与原来的链接对比，我们就可以用正则表达式改写收藏页面的链接，从而直接获得原图图片

![origin](https://github.com/pwjworks/Pixiv_spider/blob/master/img_folder/original_url.PNG)

![mid](https://github.com/pwjworks/Pixiv_spider/blob/master/img_folder/mid_url2.PNG)

    original_url = url.replace("c/150x150/img-master", "img-original").replace("_master1200", "")
    
 这样就获得了原图链接，但是下载时访问原图还需要把referer_url加上（referer_url就是收藏页面点进去的地址，如：https://www.pixiv.net/member_illust.php?mode=medium&illust_id=70291526），
 否则服务器会返回403错误
 
 **3.下载系列图片**
 
 pixiv中有许多系列图片，只使用以上方法只能爬去系列图片中的一张，打开收藏页面，可以发现图片数量的标签
 
 ![multiple](https://github.com/pwjworks/Pixiv_spider/blob/master/img_folder/mutiple.PNG)
 
 在系列图片下，第一张对应的是p0，第二张对应的是p1,如此类推..
 
 ![p0](https://github.com/pwjworks/Pixiv_spider/blob/master/img_folder/p0.PNG)
 ![p1](https://github.com/pwjworks/Pixiv_spider/blob/master/img_folder/p1.PNG)
 
 
