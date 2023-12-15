## 日常blog使用的脚本

get_summary利用gpt3.5获取文章摘要

push_to_gzh同步文章到微信公众号脚本

push_to_xiaohongshu 将html按照文章章节转换成图片，然后通过图文模式发布到小红书

## push_to_gzh 说明

此项目本质上是将md文件转换成html文件，然后通过公众号的接口推送到公众到草稿箱，通过手动点击发布

### 使用介绍

1. push_to_gzh\config.ini 中md_dir为需要推送到公众号的文章目录，文章目前只支持md格式
2. push_to_gzh\app.py 为启动文件
3. push_to_gzh\styles_renderer.py中render_article函数将md文件按照指定个模板转换成html文件
    1. push_to_gzh\template\author 中按文件夹存放不同元素的模板
    2. push_to_gzh\styles\custom\cp_article_wx.ini 中配置元素使用的模板
4. push_to_gzh\sync.py 负责与公众号通信
    1. 通过WeRoBot库获取公众号token，APP_ID和APP_SECRET参数在公众号后台获取，注意在公众号后台设置白名单IP
    2. 通过WeRoBot上传文章中的图片素材，通过API将文章对应的html发布到草稿箱