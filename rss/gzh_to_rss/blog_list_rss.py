import concurrent.futures
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import threading
import requests
from bs4 import BeautifulSoup
from lib.file_manager import FileManager

# 定义一个锁
lock = threading.Lock()

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

def get_recent_article(url,channel,start_time,end_time):
    ## 获取对应XML信息
    try:
        response = requests.get(url=url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'})
        content_type = response.headers.get('Content-Type')

        # 检查是否有charset=utf-8
        if 'charset=utf-8' in content_type:
            xml = response.text
        else:
        # 如果不是UTF-8，可以尝试手动转换编码
            xml = response.content.decode('utf-8', errors='ignore')
    except requests.exceptions.SSLError as err:
        print('SSL Error. Adding custom certs to Certifi store...')
    # 加载XML文件,获取根元素
    try:
        # 查找最新的文章
        new_rss = ET.fromstring(xml)
        # new_root = new_rss.getroot()
        # # mew_channel = ET.SubElement(new_rss, 'channel')
        new_channel = new_rss.find('channel')
        if new_channel is None:
            return url + " fail"
        # 使用锁来同步访问
        with lock:
            for item in new_channel.findall('item'):
                node = item.find('pubDate')
                if node is not None and node.text != "":
                    # 将日期时间字符串转换为时间对象
                    if node.text.endswith("GMT"):
                        pubDate = datetime.strptime(node.text, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=None)
                    else:
                        pubDate = datetime.strptime(node.text, "%a, %d %b %Y %H:%M:%S %z").replace(tzinfo=None)
                    ns1 = item.find(".//{http://purl.org/rss/1.0/modules/content/}encoded")
                    if ns1 is not None:
                        item.remove(ns1)
                    ## 将内容写入文件中
                    if pubDate > start_time and pubDate < end_time:
                        first_item = channel.find('item')
                        if first_item is not None:
                            channel.insert(list(channel).index(first_item), item)
                        else:
                        # 如果没有其他item元素，直接追加到channel元素
                            channel.append(item)
            return url + " successe"
    except ET.ParseError:
        return url + " fail"

def get_blog_list(url,start_time,end_time):
    ## 获取对应网页html
    try:
        html = requests.get(url=url, headers='').text
    except requests.exceptions.SSLError as err:
        print('SSL Error. Adding custom certs to Certifi store...')
    ## 获取不同博客名和对应RSS订阅地址
    name_list,url_list = get_list_name_url(html)
    # 创建或加载新的RSS文件树和根元素
    rss = ET.parse(r'D:\workspace\script\gzh_to_rss\rss.xml')
    root = rss.getroot()
    channel = root.find('channel')
    last_build_date = channel.find('lastBuildDate')
    pubDate = channel.find('pubDate')
    if last_build_date is not None:
        last_build_date.text = end_time.strftime('%a, %d %b %Y %H:%M:%S %z')
    if pubDate is not None:
        pubDate.text = end_time.strftime('%a, %d %b %Y %H:%M:%S %z')
    # channel = ET.SubElement(rss, 'channel')
    # 提交任务给线程池，并获取Future对象
    futures = []
    # 创建线程池
    executor = concurrent.futures.ThreadPoolExecutor()
    for i in range(len(url_list)):
        future = executor.submit(get_recent_article,url_list[i],channel,start_time,end_time)
        futures.append(future)

    # 获取任务的返回值
    # results = []
    for future in concurrent.futures.as_completed(futures):
        result = future.result()
        print(result)
        # results.append(result)
    # 关闭线程池
    executor.shutdown()
    #将最终结果写入文件
    with lock:
        for item in channel.findall('item'):
            node = item.find('pubDate')
            if node is not None and node.text != "":
                # 将日期时间字符串转换为时间对象
                if node.text.endswith("GMT"):
                    pubDate = datetime.strptime(node.text, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=None)
                else:
                    pubDate = datetime.strptime(node.text, "%a, %d %b %Y %H:%M:%S %z").replace(tzinfo=None)
                if pubDate < end_time - timedelta(days=3):
                    channel.remove(item)
        rss.write(r'D:\workspace\script\gzh_to_rss\rss.xml', encoding='UTF-8', xml_declaration=True)
    print("write rss done")

def up_data_filebrowser():
    file_mgr = FileManager()
    file_mgr.upload_file(remote_file_path="rss.xml", local_file_path="D:\\workspace\\script\\gzh_to_rss\\rss.xml", should_override=True)

if __name__ == "__main__":
    ## 定时查询
    end_time = datetime.now()
    start_time = end_time - timedelta(days=1)
    ## 获取最近一周内发表的文章
    get_blog_list("https://wechat2rss.xlab.app/list/all.html",start_time,end_time)
    # up_data_filebrowser()
