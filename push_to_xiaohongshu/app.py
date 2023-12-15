import os.path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from upload_xiaohongshu import get_driver,xiaohongshu_login,publish_xiaohongshu_image

def html_to_png(html_path,out_path): 
    # options = webdriver.ChromeOptions()
    options = webdriver.EdgeOptions()
    options.add_argument('--headless')  # 不知为啥只能在无头模式执行才能截全屏
    options.add_argument('--disable-gpu')
    driver = webdriver.Edge(options=options)
    # driver = webdriver.Chrome(options=options)
    driver.maximize_window()

    try:
        driver.get(html_path)
        sections = driver.find_elements(By.XPATH, "//h3 | //h4")
        h3_height_list = []
        for section in sections:    
            # 使用JavaScript执行脚本来获取章节元素在网页中的位置信息
            location = driver.execute_script("return arguments[0].getBoundingClientRect();", section)
            h3_height_list.append((location['left'],location['top']))

        index = 0
        size = []
        scroll_width = driver.execute_script('return document.body.parentNode.scrollWidth')
        scroll_height = driver.execute_script('return document.body.parentNode.scrollHeight')
        driver.set_window_size(scroll_width, scroll_height)
        driver.get_screenshot_as_file(out_path + "screenshot.png")
        for item in h3_height_list:
            if index > 0:
                screenshot = Image.open(out_path + "screenshot.png")
                # 裁剪出感兴趣的位置
                cropped_image = screenshot.crop((0, int(size[1]), scroll_width, int(item[1])))
                # 保存裁剪后的图片
                cropped_image.save(out_path + "%d.png" % index)
            size = item
            index += 1
        cropped_image = screenshot.crop((0, int(size[1]), scroll_width, scroll_height))
        # 保存裁剪后的图片
        cropped_image.save(out_path + "%d.png" % index)
        os.remove(out_path + "screenshot.png")
        driver.quit()
    except Exception as e:
        print(e)



if __name__ == '__main__':
    _HTML = 'D:\\workspace\\script\\push_to_gzh\\article\\out\\index_cp_article_wx.html'
    _OUTFILE = 'D:\\workspace\\script\\push_to_xiaohongshu\\out\\'
    title = 'tips：关闭自动扣费服务'   ## 小红书标题
    describe = "一般情况下，大部分APP自动续费扣费时间节点设置在到期前1天，消费者只要在到期前1天手动操作取消。但是也有少量APP的扣费时间节点较为模糊，更有个别APP竟然提前3天就扣费了。\n如果你不记得之前办理了哪些“自动续费”服务，那就不妨进入微信和支付宝的支付设置，在里面找到“扣费”的选项，就能看到通过微信和支付宝进行自动续费的服务，点击它们就能取消自动续费合约\n”微信：打开微信，点击【我的】—【服务】-【钱包】-【支付设置】-【自动续费】，检查和选择要关闭的扣款项目。\n支付宝：打开支付宝，点击【我的】—【设置】—【支付设置】—【自动扣款】，检查和选择要关闭的扣款项目。\n"  ## 描述
    keywords = ['#小技巧','#tips','#自动扣费','#支付宝','#微信']  ## 标签

    # 首先创建一个保存截图的文件夹
    if not os.path.isdir(_OUTFILE):
        # 判断文件夹是否存在，如果不存在就创建一个
        os.makedirs(_OUTFILE)
    # 将html转换成png
    # html_to_png("file:///"+_HTML,_OUTFILE)
    try:
        driver = get_driver()
        xiaohongshu_login(driver=driver)
        publish_xiaohongshu_image(driver,_OUTFILE, title,describe,keywords)
    finally:
        driver.quit()