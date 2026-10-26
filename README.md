## 日常脚本介绍

- get_summary: 利用gpt3.5获取文章摘要
- push_to_gzh: 同步文章到微信公众号脚本
- push_to_xiaohongshu: 将html按照文章章节转换成图片，然后通过图文模式发布到小红书
- copyBook: 小说爬虫脚本和Django图书网站，样式与一般网络小说网站类似
- mytools: windows日常工具，包含加解密/时间戳转换/pdf合并/汇率计算
- gzh_to_rss: 公众号内容转换成RSS,用于feedly订阅
- xiaohongshu: 支持搜索小红书，搜索到的文章导出为execel
- m3u8: mu38视频下载脚本
- xs: 香色闺阁书源解密，阅读源转换成香色源，语音tts相关脚本
- chrome: 自己写的chrome脚本和插件
- qinglong: 自己日常使用的青龙脚本
- tq: 泰坦之旅百科 - Flask Web 应用
- douyu: douyu插件
- twitter: X视频下载插件

### 斗鱼通用多屏与声源选择

- 普通直播间可使用播放器底部控制栏右侧的“通用多屏”入口：输入数字房间号或对应的斗鱼直播间链接，手动添加副屏，无需平台下发联播配置。入口随控制栏显示或隐藏，菜单向上展开并保持右对齐。
- 通用多屏最多同时观看 5 个直播间（当前房间 + 4 个副屏），支持重试、移除及一键退出。当前直播间保持原播放器，副屏复用脚本已有的斗鱼直播流接口。
- 房间提供官方多屏入口或正在使用官方多屏时，不展示“通用多屏”，无需先进入官方多屏播放；运行期间检测到官方多屏后会退出通用多屏，优先保留平台原有的联播功能。未开播、权限受限、接口或网络异常的直播间会显示错误，不保证所有直播流都能播放。
- 在斗鱼播放器中开启平台多屏或添加通用多屏副屏后，右下角会显示“多屏声源”菜单，可选择收听当前直播间或某个副屏。
- 同一时间只播放所选屏幕的声音；菜单内支持音量调节和静音，播放器原生音量条、静音按钮及音量区域的滚轮也控制所选声源；播放器获得焦点后可使用上下方向键调节音量。
- 副屏重载后保留声源选择；所选副屏被移除或退出多屏时，声音切回当前直播间，并保留调整后的音量和静音状态。
- 声源选择支持平台多屏与通用多屏，不控制脚本原有的浮窗播放器。
- 通用多屏回归测试：`node --test douyu\douyuex.multiscreen.test.cjs`（在仓库根目录执行）。

## 脚本详情

### get_summary

- 遍历博客目录，未生成简介的文章，使用GPT3.5 API获取简介

### push_to_gzh

1. 此项目本质上是将md文件转换成html文件，然后通过公众号的接口推送到公众到草稿箱，通过手动点击发布
2. push_to_gzh\config.ini 中md_dir为需要推送到公众号的文章目录，文章目前只支持md格式
3. push_to_gzh\app.py 为启动文件
~~4. push_to_gzh\styles_renderer.py中render_article函数将md文件按照指定个模板转换成html文件~~
    ~~1. push_to_gzh\template\author 中按文件夹存放不同元素的模板~~
    ~~2. push_to_gzh\styles\custom\cp_article_wx.ini 中配置元素使用的模板~~
4. push_to_gzh\bm_md_renderer.py 使用bm.md服务对md文件进行转换
5. push_to_gzh\sync.py 负责与公众号通信
    1. 通过WeRoBot库获取公众号token，APP_ID和APP_SECRET参数在公众号后台获取，注意在公众号后台设置白名单IP
    2. 通过WeRoBot上传文章中的图片素材，通过API将文章对应的html发布到草稿箱

### push_to_xiaohongshu

- 利用selenium实现自动化发小红书
    1. 支持编写文章文字、打标签、发图片
    2. 支持将html页面转换成图片，然后通过图片发布

### copyBook

- [使用文档](./copyBook/README.md)
- 丰富了爬虫脚本，支持24hbook.com,beitai.cc,shuqi.com
    1. 24hbook.com格式为epub
    2. beitai.cc下载格式为rar
    3. shuqi.com勉强可用

### mytools

1. 编译后exe过大，上传不便,自行编译
2. 控制台进入mytools目录，执行pyinstaller.exe main.spec

### rss

#### follow

1. follow网站拷贝https://api.follow.is/entries 接口返回的json信息
2. 批量获取json中的rss 地址，替换为可用地址并合成opml文件，方便订阅

#### gzh_to_rss

1. 基于公众号转成rss的聚合服务[wechat2rss](https://github.com/ttttmr/wechat2rss)加工
2. 定时分析聚合服务中更新的文章编写成RSS文件，通过minio服务提供文件访问

### xiaohongshu

1. 支持搜索小红书内容，并导出为excel
2. 需要自行抓包获取Authorization参数，推荐抓取小红书微信小程序

### m3u8

1. m3u8视频下载工具
2. 修改m3u8_url，output_file，response = requests.get( 中的地址，下载视频

### xs

1. xbstools.py提供xbs与json互转能力
2. tts封装 Azure/Ali/Edge tts服务，voice_list.py获取Azure TTS音色列表
3. data 包含部分源和js解析案例，提高编写源的效率，香色中未集成CryptoJS，需要使用时，需要放入js解析中
4. url_check.py 检测书源是否可用，需要配合xbstools.py使用
5. ydstools.py 提供yds与json互转能力
6. test.js 用于测试香色中js解析模块对应js代码运行是否正常

### chrome
1. url_check，浏览器加载此文件夹即可安装，点击后检测书签是否可用，将不可用的书签罗列出来，方便删除
2. cnn，浏览器加载此文件夹即可安装，点击后展示CNNFear & Greed Index曲线图，刚安装只有1天的数据
3. get-cookies,获取当前页面cookies,fork https://github.com/kairi003/Get-cookies.txt-LOCALLY/ 调整而来
4. markdown ，将markdown内容转换成chrome可导入的书签文件
5. seckill，自动化点击插件，还未修复完

### qinglong
1. qdii_parser.py, LOF基金套利信息通知，代码中通知到zulip，自行修改为其他渠道
2. hxsy.py, iOS 收费APP网站打卡
3. weather_to_zulip.py,获取最近7天天气

### tq
1. 获取泰坦之旅chm资料，解压到本地
2. 使用大模型分析本地资料，并编写前后端代码，方便在网页上查看
3. python app.py启动服务，通过ip:5000或者绑定域名进行查看 