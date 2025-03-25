import concurrent.futures
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import threading
import requests
from bs4 import BeautifulSoup
from lib.file_manager import FileManager
# 代理配置
PROXIES = {
    'http': 'http://127.0.0.1:1080',  # 本地代理端口，根据实际情况修改
    'https': 'http://127.0.0.1:1080'
}

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_list_name_url(html):
    # 创建BeautifulSoup对象bito.ai
    soup = BeautifulSoup(html, 'html.parser')

    # 提取博客名称和RSS地址内容
    name_list = []
    url_list = []
    paragraph = soup.find_all('div', class_='vp-doc _list_all')
    for parent in paragraph:
        span_a_content = parent.find_all(name='p')
        for a_content in span_a_content:
            name_list.append(a_content.find('a').text)
            url_list.append(a_content.find('a')['href'])
    return name_list, url_list

def get_blog_list(url):
    ## 获取对应网页html
    try:
        html = requests.get(url=url, headers=HEADERS,proxies=PROXIES).text
    except requests.exceptions.SSLError as err:
        print('SSL Error. Adding custom certs to Certifi store...')
    ## 获取不同博客名和对应RSS订阅地址
    name_list,url_list = get_list_name_url(html)
    # 创建或加载新的RSS文件树和根元素
    rss = ET.parse(r'D:\workspace\script\rss\gzh_to_rss\rss.opml')
    root = rss.getroot()
    channel = root.find('body')
    item = channel.find('outline')
    for name, url in zip(name_list, url_list):
        outline = ET.SubElement(item, 'outline')
        outline.set('text', name)
        outline.set('title', name)
        outline.set('type', 'rss')
        outline.set('xmlUrl', url)
    # 保存XML
    rss.write(r'D:\workspace\script\rss\gzh_to_rss\rss.opml', encoding='UTF-8', xml_declaration=True)
    print("write rss done")

if __name__ == "__main__":
    get_blog_list("https://wechat2rss.xlab.app/list/all.html")