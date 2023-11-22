import os.path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By


def webshot(html_path,out_path): 
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 不知为啥只能在无头模式执行才能截全屏
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)
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
        # height = 0
        # index = 0
        # 返回网页的高度的js代码
        # js_height = "return document.body.clientHeight"
        # current_height = driver.execute_script("return document.body.clientHeight")
        # total_height = driver.execute_script("return document.documentElement.scrollHeight")
        # while height < total_height:
        #     if index + 1 < len(h3_height_list):
        #         if(current_height < h3_height_list[index+1]):
        #             js_move = "window.scrollTo(0,{})".format(h3_height_list[index+1])
        #             driver.execute_script(js_move)
        #         driver.set_window_size(1280, h3_height_list[index+1]- h3_height_list[index])
        #     else:
        #         js_move = "window.scrollTo(0,{})".format(total_height)
        #         driver.execute_script(js_move)
        #         driver.set_window_size(1280, total_height - h3_height_list[index])
        #     driver.get_screenshot_as_file(out_path + "%d.png" % index)
        #     index += 1
        #     height += h3_height_list[index+1]
        #     print('%d %d' % (height,total_height))
        driver.quit()
    except Exception as e:
        print(e)

if __name__ == '__main__':
    _HTML = 'D:\workspace\\script\\push_to_gzh\\article\\out\\index_cp_article_wx.html'
    _OUTFILE = 'D:\\workspace\\script\\push_to_xiaohongshu\\out\\'
    # 首先创建一个保存截图的文件夹
    if not os.path.isdir(_OUTFILE):
        # 判断文件夹是否存在，如果不存在就创建一个
        os.makedirs(_OUTFILE)
    webshot("file:///"+_HTML,_OUTFILE)