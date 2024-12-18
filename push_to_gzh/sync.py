#!/usr/bin/python3
##public/upload_news.py
# -*- coding: utf-8 -*-
"""
推送文章到微信公众号
"""
import urllib
import os.path
import hashlib
import pickle
import requests
import json
import urllib.request
import html
import re

from pyquery import PyQuery
from werobot import WeRoBot
from datetime import datetime

class BaseInfo:
    def __init__(self, content,mediaId,path):
        self.TITLE = self.fetch_attr(content, 'title').strip('"').strip('\'')
        self.THUMB_MEDIA_ID = mediaId
        self.AUTHOR = '阿松日常'
        link = path.split(os.sep)[-2].lower()
        self.link = link.split('/content/posts/')[-1]
        ### 摘要
        self.digest = self.fetch_attr(content, 'summary').strip().strip('"').strip('\'')
        self.CONTENT_SOURCE_URL = 'https://xiaoshame.github.io/posts/{}'.format(self.link)
     
    def fetch_attr(self,content, key):
        """
        从markdown文件中提取属性
        """
        lines = content.split('\n')
        for line in lines:
            if line.startswith(key):
                return line.split(':')[1].strip()
        return ""

CACHE = {}

CACHE_STORE = r"D:/workspace/script/push_to_gzh/article/cache.bin"

def dump_cache():
    fp = open(CACHE_STORE, "wb")
    pickle.dump(CACHE, fp)

def init_cache():
    global CACHE
    if os.path.exists(CACHE_STORE) and os.path.getsize(CACHE_STORE) > 0:      
        with open(CACHE_STORE, "rb") as fp:
            unpickler = pickle.Unpickler(fp)
            CACHE = unpickler.load()
            return
    dump_cache()

def Client():
    robot = WeRoBot()    
    robot.config["APP_ID"] = os.environ.get("WX_GZH_APP_ID")
    robot.config["APP_SECRET"] = os.environ.get("WX_GZH_APP_SECRET")
    client = robot.client
    token = client.grant_token()
    return client, token['access_token']

def cache_get(key):
    if key in CACHE:
        return CACHE[key]
    return None


def file_digest(file_path):
    """
    计算文件的md5值
    """
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        md5.update(f.read())
    return md5.hexdigest()

def cache_update(file_path):
    digest = file_digest(file_path)
    CACHE[digest] = "{}:{}".format(file_path, datetime.now())
    dump_cache()

def file_processed(file_path):
    digest = file_digest(file_path)
    return cache_get(digest) != None

def upload_image_from_path(client,image_path):
  image_digest = file_digest(image_path)
  res = cache_get(image_digest)
  if res != None:
      return res[0], res[1]
  print("uploading image {}".format(image_path))
  try:
    media_json = client.upload_permanent_media("image", open(image_path, "rb")) ##永久素材
    media_id = media_json['media_id']
    media_url = media_json['url']
    CACHE[image_digest] = [media_id, media_url]
    dump_cache()
    print("file: {} => media_id: {}".format(image_path, media_id))
    return media_id, media_url
  except Exception as e:
    print("upload image error: {}".format(e))
    return None, None

def upload_image(client,img_url):
  """
  * 上传临时素菜
  * 1、临时素材media_id是可复用的。
  * 2、媒体文件在微信后台保存时间为3天，即3天后media_id失效。
  * 3、上传临时素材的格式、大小限制与公众平台官网一致。
  """
  resource = urllib.request.urlopen(img_url)
  name = img_url.split("/")[-1]
  f_name = "D:/workspace/tmp/{}".format(name)
  if "." not in f_name:
    f_name = f_name + ".png"
  with open(f_name, 'wb') as f:
    f.write(resource.read())
  return upload_image_from_path(client,f_name)

def get_images_from_markdown(content):
    lines = content.split('\n')
    images = []
    for line in lines:
        line = line.strip()
        if 'featuredImage :' in line:
            image = line.split('featuredImage :')[1].strip()
            images.append(image)  
        if  '![' in line and line.endswith(')'):
            image = line.split('(')[1].split(')')[0].strip()
            images.append(image)
    return images

def update_images_urls(content,client):
    images = get_images_from_markdown(content)
    uploaded_images = {}
    for image in images:
        media_id = ''
        media_url = ''
        if image.startswith("http"):
            media_id, media_url = upload_image(client,image)
        else:
            media_id, media_url = upload_image_from_path(client,"D:/workspace/blog/static" + image)
        if media_id != None:
            uploaded_images[image] = [media_id, media_url]
    for image, meta in uploaded_images.items():
        orig = "({})".format(image)
        new = "({})".format(meta[1])
        #print("{} -> {}".format(orig, new))
        content = content.replace(orig, new)
    return content,uploaded_images[images[0]][0]

def upload_media_news(content,baseinfo,token):
    """
    上传到微信公众号素材
    """
    articles = {
        'articles':
        [
            {
                "title": baseinfo.TITLE,
                "thumb_media_id": baseinfo.THUMB_MEDIA_ID,
                "author": baseinfo.AUTHOR,
                "digest": baseinfo.digest,
                "show_cover_pic": 1,
                "content": content,
                "content_source_url": baseinfo.CONTENT_SOURCE_URL
            }
            # 若新增的是多图文素材，则此处应有几段articles结构，最多8段
        ]
    }

    headers={'Content-type': 'text/plain; charset=utf-8'}
    datas = json.dumps(articles, ensure_ascii=False).encode('utf-8')
    
    # 发布草稿箱
    postUrl = "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=%s" % token
    r = requests.post(postUrl, data=datas, headers=headers)
    try:
        resp = json.loads(r.text)
        media_id = resp['media_id']
        print(media_id)
        # ### 发布
        # media_params = {
        #     "media_id": media_id
        # }
        # postUrl = "https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token=%s" % token
        # datas = json.dumps(media_params, ensure_ascii=False).encode('utf-8')
        # r = requests.post(postUrl,data=datas, headers=headers)
        # resp = json.loads(r.text)
        # print(resp)
        return True
    except json.JSONDecodeError as e:
        # 捕获JSON解码错误
        print("Invalid JSON:", e)
        print(r.text)
        return False
    except KeyError as e:
        # 捕获键错误
        print("Key Error:", e)
        print(r.text)
        return False

def replace_para(content):
    res = []
    for line in content.split("\n"):
        if line.startswith("<p>"):
            line = line.replace("<p>", gen_css("para"))
        res.append(line)
    return "\n".join(res)


def replace_header(content):
    res = []
    for line in content.split("\n"):
        l = line.strip()
        if l.startswith("<h") and l.endswith(">") > 0:
            tag = l.split(' ')[0].replace('<', '')
            value = l.split('>')[1].split('<')[0]
            digit = tag[1]
            font =  (18 + (4 - int(tag[1])) * 2) if (digit >= '0' and digit <= '9') else 18
            res.append(gen_css("sub", tag, font, value, tag))
        else:
            res.append(line)
    return "\n".join(res)


def fix_image(content):
    pq = PyQuery(content)
    imgs = pq('img')
    for line in imgs.items():
        link = """<img alt="{}" src="{}" />""".format(line.attr('alt'), line.attr('src'))
        figure = gen_css("figure", link, line.attr('alt'))
        content = content.replace(link, figure)
    return content

def format_fix(content):
    content = content.replace("\n", "")
    content = re.sub(r'>\s+</strong>\s+<','></strong><', content)
    content = re.sub(r'>\s+<strong>','><strong>', content)
    content = re.sub(r'</strong>\s+<','</strong><', content)
    content = re.sub(r'>\s+<section','><section', content)
    
    content = content.replace("<code>", gen_css("code"))   ## 保障代码过长的代码换行
    content = content.replace("""<pre style="line-height: 125%">""", """<pre style="line-height: 125%; color: white; font-size: 11px;">""")
    return content

def css_beautify(content):
    content = replace_para(content)
    # content = replace_header(content)
    content = replace_links(content)
    content = format_fix(content)
    content = fix_image(content)
    content = gen_css("header") + content + "<p>文章不定期修改，因公众号无法同步修改，查看最新内容点击左下角“阅读原文”<p>" + "</section>"
    return content

def has_multiple_values(lst, param):
    count = 0
    for item in lst.items():
        if  item.text() == param:
            count += 1
            if count > 1:
                return True
    return False

def array_include_values(lst,param):
    count = 0
    for item in lst:
        if  item[1] == param:
                return True
    return False

def replace_links(content):
    pq = PyQuery(content)
    links = pq('a')
    refs = []
    index = 1
    if len(links) == 0:
        return content
    for l in links.items():
        link = gen_css("link", l.text(), index)
        if has_multiple_values(links,l.text()) == True and array_include_values(refs,l.text()) == True:
            continue
        index += 1
        refs.append([l.attr('href'), l.text(), link])

    for r in refs:
        orig = "<a href=\"{}\">{}</a>".format(html.escape(r[0]), r[1])
        print(orig)
        content = content.replace(orig, r[2])
    ### 添加参考资料
    content = content + "\n" + gen_css("ref_header1","参考资料")
    ### 引用链接垂直排列
                    
    content += '''<span style="display: flex;flex-direction :column;">'''
    index = 1
    for r in refs:
        l = r[2]
        line = gen_css("ref_link1", index, r[1], r[0])
        index += 1
        content += line + "\n"
    content += '</span>'
    return content

def gen_css(path, *args):
    file_path = os.path.join(os.path.split(os.path.realpath(__file__))[0],"template/author/assets") + "/{}.tmpl".format(path)
    tmpl = open(file_path, "r").read()
    return tmpl.format(*args)
