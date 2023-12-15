import csv
import hashlib
import json
import os
import re
import time
from urllib import parse

import requests

# import urllib3

# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_x_sign(api):
    x_sign = "X"
    m = hashlib.md5()
    m.update((api + "WSUDD").encode())
    x_sign = x_sign + m.hexdigest()
    return x_sign


def get_proxy():
    return requests.get("http://0.0.0.0:5010/get/").text

# #api地址
# def header():
#     headers = {
#     'Accept-Encoding':'gzip, deflate, br',
#     'Accept-Language':'zh-cn',
#     'Connection':'keep-alive',
#     'Device-Fingerprint':'',
#    # 'Cookie':,
#     'Host':'www.xiaohongshu.com',
#     'Referer':'https://servicewechat.com/wxffc08ac7df482a27/346/page-frame.html',
#     'User-Agent':'Mozilla\/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit\/605.1.15 (KHTML, like Gecko) Mobile\/15E148 MicroMessenger\/8.0.39(0x18002733) NetType\/WIFI Language\/zh_CN',
#     'Authorization':,
#     }
#     return headers


def html_header(url):
    headers = {
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-cn',
        'Connection': 'keep-alive',
        'Device-Fingerprint': '',
        'Cookie': '',
        'Host': 'www.xiaohongshu.com',
        'User-Agent': 'Mozilla\/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit\/605.1.15 (KHTML, like Gecko) Mobile\/15E148 MicroMessenger\/8.0.39(0x18002733) NetType\/WIFI Language\/zh_CN',
        'X-Sign': get_x_sign(url),
    }
    return headers


def setxhs(url, referer):
    headers = {
        'User-Agent': 'Mozilla\/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit\/605.1.15 (KHTML, like Gecko) Mobile\/15E148 MicroMessenger\/8.0.39(0x18002733) NetType\/WIFI Language\/zh_CN',
        'Referer': referer,
        'Authorization': 'wxmp.e441520c-acec-4390-97c5-a06c0ef8184d',  # 在这里填入抓到的header
        'X-Sign': get_x_sign(url)
    }
    return headers


# 解析Json数据
# def getJsonSession(url):
#     ses = requests.session()
#     html = ses.get(url, headers=header(), verify=False)
#     soup = json.loads(html.text)
#     return soup
# 解析HTML页面


# def getHtmlSession(url):
#     ses = requests.session()
#     html = ses.get(url, headers=html_header(url), verify=False).text
#     # 写入内容到文件
#     file = open("example.txt", "w", encoding='utf-8')
#     file.write(html)
#     file.close()
#     soup = BeautifulSoup(html, 'html.parser')
#     return html


def getData(bookUrl):
    picUrls = []
    ses = requests.session()
    html = ses.get(bookUrl, headers=html_header(bookUrl), verify=False).text

    # 将html转化为json
    start = html.find("<script>window.__INITIAL_STATE__=")
    end = html.find("</script>", start)
    json_str = html[start+33:end]
    json_data = json.loads(json_str)
    # file = open("example.json", "w", encoding='utf-8')
    # file.write(json_str)
    # file.close()
    # 解析json，获取文章内容和图片地址
    content = json_data['noteData']['data']['noteData']['desc']
    pics = json_data['noteData']['data']['noteData']['imageList']
    for pic in pics:
        picUrl = pic['url']
        picUrls.append(picUrl)
        # print(picUrl)
    return content, picUrls


def download_image(urls, dirs):
    path = replace_non_chinese_characters(dirs)
    base_path = os.path.split(os.path.realpath(__file__))[0] + "/list/" 
    create_folder(base_path + path)
    # 遍历链接列表并下载图片
    for idx, url in enumerate(urls):
        output_file = base_path + path + f"/image{idx+1}.jpg"
        response = requests.get("https:"+url)
        if response.status_code == 200:
            with open(output_file, 'wb') as f:
                f.write(response.content)


def replace_non_chinese_characters(input_string, replacement=''):
    pattern = r'[^\u4e00-\u9fff]'
    replaced_string = re.sub(pattern, replacement, input_string)
    return replaced_string


def create_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"文件夹 {folder_path} 创建成功")
    else:
        print(f"文件夹 {folder_path} 已存在")


def request(url, headers, timeout):
    html = requests.get(url=url, headers=headers, verify=False).text
    # print(html)
    content = json.loads(html)
    path = os.path.split(os.path.realpath(__file__))[0] + '/list/list.csv'
    f = open(path, 'a+', encoding='utf-8-sig', newline='')  # a+表示追加
    csv_writer = csv.writer(f)
    csv_writer.writerow(
        ['id', '标题', '内容', '喜欢', '用户名', '图片地址', '发布时间'])
    for i in range(len(content["data"]["notes"])):
        id = content["data"]["notes"][i]["id"]
        title = content["data"]["notes"][i]["title"]
        # img_user = content["data"]["notes"][i]["user"]["image"]
        like = content["data"]["notes"][i]["likes"]
        user = content["data"]["notes"][i]["user"]["nickname"]
        # user_id = content["data"]["notes"][i]["user"]["id"]
        create_time = content["data"]["notes"][i]["time"]
        # # 爬取指定时间之后的文章
        # custom_date = datetime.datetime.strptime(create_time, "%Y-%m-%d %H:%M")
        # timestamp = custom_date.timestamp()
        # if timestamp <= 1694275200:
        #     continue
        if like <= 10:
             continue
        # 获取文章内容
        note_url = "https://www.xiaohongshu.com/discovery/item/" + str(id)
        desc, pics = getData(note_url)
        download_image(pics, title)
        # 睡眠5秒
        time.sleep(2)
        csv_writer.writerow(
            [id, title, desc, like, user, pics, create_time])
    f.close()


def spider(keyword, d_page, sort_by='general'):
    """
    :param keyword:
    :param d_page: 页数
    :param sort_by: general：综合排序，hot_desc：热度排序
    :return:
    """
    host = 'https://www.xiaohongshu.com'
    # page 从0开始, 所以这里+1
    url = '/fe_api/burdock/weixin/v2/search/notes?keyword={}&sortBy={}' \
          '&page={}&pageSize=20&prependNoteIds=&needGifCover=true'.format(parse.quote(keyword),sort_by, d_page + 1)
    referer = 'https://servicewechat.com'
    headers = setxhs(url, referer)
    # proxies = {'http': "http://{}".format(get_proxy())}
    # 记得使用代理池
    request(url=host + url, headers=headers, timeout=5)


if __name__ == "__main__":
    spider("博客", d_page=1)
