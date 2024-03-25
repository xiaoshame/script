# -*- coding: utf-8 -*-
import os

import requests
import re
import json

import os.path

import execjs


def decode(self,data):
    path = os.path.split(os.path.realpath(__file__))[0] + '/shuqi.js'
    with open(path, 'r', encoding='UTF-8') as f:
        js_code = f.read()
        context = execjs.compile(js_code)
        result = context.call("decodeCont", data)
        return result

def get_search_code(url):
    search = "/modules/article/search.php"
    url = url + search  # 替换为你想要请求的URL
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
    }
    data = {
        'searchkey': '天之下',
        'searchtype': 'all',
        'page':'1',
        # 添加更多键值对作为需要
    }

    response = requests.get(url, data=data,headers=headers)

    # 检查请求是否成功
    if response.status_code == 200:
        path = os.path.split(os.path.realpath(__file__))[0] + '/69shu.js'
        with open(path, 'r', encoding='UTF-8') as f:
            js_code = f.read()
            context = execjs.compile(js_code)
            result = context.call("get_chapter",response.text)
    else:
        # 请求失败，打印错误信息
        print('请求失败，状态码：', response.status_code)


if __name__ == "__main__":
    os.environ["HTTP_PROXY"] = "http://127.0.0.1:1081"
    os.environ["HTTPS_PROXY"] = "http://127.0.0.1:1081"
    get_search_code("https://69shu.pro")