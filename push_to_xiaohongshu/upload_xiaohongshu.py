import json
import os
import time
import traceback
from datetime import datetime,timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

XIAOHONGSHU_COOKING = r'D:\workspace\script\push_to_xiaohongshu\out\config.json'

def get_driver():
    options = webdriver.EdgeOptions()
    # options.add_argument('--headless')  # 不知为啥只能在无头模式执行才能截全屏
    # options.add_argument('--disable-gpu')
    driver = webdriver.Edge(options=options)
    driver.maximize_window()

    return driver

def xiaohongshu_login(driver):
    if (os.path.exists(XIAOHONGSHU_COOKING)):
        print("cookies存在")
        with open(XIAOHONGSHU_COOKING) as f:
            cookies = json.loads(f.read())
            driver.get("https://creator.xiaohongshu.com/creator/post")
            driver.implicitly_wait(10)
            driver.delete_all_cookies()
            time.sleep(4)
            # 遍历cook
            print("加载cookie")
            for cookie in cookies:
                if 'expiry' in cookie:
                    del cookie["expiry"]
                # 添加cook
                driver.add_cookie(cookie)
            # 刷新
            print("开始刷新")
            driver.refresh()
            driver.get("https://creator.xiaohongshu.com/publish/publish")
            time.sleep(5)
    else:
        print("cookies不存在")
        driver.get('https://creator.xiaohongshu.com/creator/post')
        # driver.find_element(
        #     "xpath", '//*[@placeholder="请输入手机号"]').send_keys("")
        # # driver.find_element(
        # #     "xpath", '//*[@placeholder="请输入密码"]').send_keys("")
        # driver.find_element("xpath", '//button[text()="登录"]').click()
        print("等待登录")
        time.sleep(30)
        print("登录完毕")
        cookies = driver.get_cookies()
        with open(XIAOHONGSHU_COOKING, 'w') as f:
            f.write(json.dumps(cookies))
        print(cookies)
        time.sleep(1)

def get_publish_date():
    tomorrow = now = datetime.today()
    if(now.hour > 20):
        tomorrow = now + timedelta(days = 1)
        tomorrow = tomorrow.replace(hour=20)
    else:
        tomorrow = tomorrow.replace(hour=20,minute=0)
    return tomorrow.strftime("%Y-%m-%d %H:%M")

def publish_xiaohongshu_video(driver, mp4, index):
    driver.find_element("xpath", '//*[text()="发布笔记"]').click()
    print("开始上传文件", mp4[0])
    time.sleep(3)
    # ### 上传视频
    vidoe = driver.find_element("xpath", '//input[@type="file"]')
    vidoe.send_keys(mp4[0])

    # 填写标题
    content = mp4[1].replace('.mp4', '')
    driver.find_element(
        "xpath", '//*[@placeholder="填写标题，可能会有更多赞哦～"]').send_keys(content)

    time.sleep(1)
    # 填写描述
    content_clink = driver.find_element(
        "xpath", '//*[@placeholder="填写更全面的描述信息，让更多的人看到你吧！"]')
    content_clink.send_keys(content)

    time.sleep(3)
    # #虐文推荐 #知乎小说 #知乎文
    for label in ["#虐文","#知乎文","#小说推荐","#知乎小说","#爽文"]:
        content_clink.send_keys(label)
        time.sleep(1)
        data_indexs = driver.find_elements(
            "class name", "publish-topic-item")
        try:
            for data_index in data_indexs:
                if(label in data_index.text):
                    print("点击标签",label)
                    data_index.click()
                    break
        except Exception:
            traceback.print_exc()
        time.sleep(1)

    # 定时发布
    dingshi = driver.find_elements(
        "xpath", '//*[@class="css-1v54vzp"]')
    time.sleep(4)
    print("点击定时发布")
    dingshi[3].click()
    time.sleep(5)
    input_data = driver.find_element("xpath", '//*[@placeholder="请选择日期"]')
    input_data.send_keys(Keys.CONTROL,'a')     #全选
    # input_data.send_keys(Keys.DELETE)
    input_data.send_keys(get_publish_date())    
    time.sleep(3)
    # driver.find_element("xpath", '//*[text()="确定"]').click()

    # 等待视频上传完成
    while True:
        time.sleep(10)
        try:
            driver.find_element("xpath",'//*[@id="publish-container"]/div/div[2]/div[2]/div[6]/div/div/div[1]//*[contains(text(),"重新上传")]')
            break
        except Exception as e:
            traceback.print_exc()
            print("视频还在上传中···")
    
    print("视频已上传完成！")
    time.sleep(3)
    # 发布
    driver.find_element("xpath", '//*[text()="发布"]').click()
    print("视频发布完成！")
    time.sleep(10)

def publish_xiaohongshu_image(driver, image_path,title,describe,keywords):
    time.sleep(3)
    driver.find_element("xpath", '//*[text()="发布笔记"]').click()
    print("开始上传图片")
    time.sleep(3)
    # ### 上传图片
    driver.find_element("xpath", '//*[text()="上传图文"]').click()
    push_file = driver.find_element("xpath", '//input[@type="file"]')
    file_names = os.listdir(image_path)
    # 打印所有文件名
    for file_name in file_names:
        push_file.send_keys(image_path + "\\"+file_name)

    # 填写标题
    driver.find_element(
        "xpath", '//*[@placeholder="填写标题，可能会有更多赞哦～"]').send_keys(title)

    time.sleep(1)
    # 填写描述
    content_clink = driver.find_element(
        "xpath", '//*[@placeholder="填写更全面的描述信息，让更多的人看到你吧！"]')
    content_clink.send_keys(describe)

    time.sleep(3)
    # #虐文推荐 #知乎小说 #知乎文
    for label in keywords:
        content_clink.send_keys(label)
        time.sleep(1)
        data_indexs = driver.find_elements(
            "class name", "publish-topic-item")
        try:
            for data_index in data_indexs:
                if(label in data_index.text):
                    print("点击标签",label)
                    data_index.click()
                    break
        except Exception:
            traceback.print_exc()
        time.sleep(1)

    # 定时发布
    dingshi = driver.find_elements(
        "xpath", '//*[@class="css-1v54vzp"]')
    time.sleep(4)
    print("点击定时发布")
    dingshi[3].click()
    time.sleep(5)
    input_data = driver.find_element("xpath", '//*[@placeholder="请选择日期"]')
    input_data.send_keys(Keys.CONTROL,'a')     #全选
    # input_data.send_keys(Keys.DELETE)
    input_data.send_keys(get_publish_date())
    time.sleep(3)
    # driver.find_element("xpath", '//*[text()="确定"]').click()

    # 发布
    driver.find_element("xpath", '//*[text()="发布"]').click()
    print("图文发布完成！")
    time.sleep(10)

if __name__ == "__main__":
    try:
        title = "测试下"
        describe = ['#python','#礼物']
        driver = get_driver()
        xiaohongshu_login(driver=driver)
        # publish_xiaohongshu_video(driver, r"D:\workspace\script\push_to_xiaohongshu\out\9.png", 1)
        publish_xiaohongshu_image(driver, r"D:\workspace\script\push_to_xiaohongshu\out", title,describe)
    finally:
        driver.quit()