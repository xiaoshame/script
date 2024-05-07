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
    title = ''   ## 小红书标题
    describe = ""  ## 描述
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