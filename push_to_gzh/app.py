# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""
-------------------------------------------------
   File     : app.py
   Author   : CoderPig
   date     : 2020-12-16 9:32 
   Desc     : 渲染生成文章
-------------------------------------------------
"""
import os.path
import config_getter
import cp_utils
import time
import sync

from bm_md_renderer import render_article, is_service_running,MARKDOWN_STYLES, CODE_THEMES


md_dir = os.path.join(os.path.split(os.path.realpath(__file__))[0], config_getter.get_config("config", "md_dir"))  # 待转换md文件路径
out_dir = os.path.join(os.path.split(os.path.realpath(__file__))[0], config_getter.get_config("config", "out_dir"))  # 输出html文件路径

# bm.md 渲染配置
MARKDOWN_STYLE = config_getter.get_config("config", "markdown_style", fallback="ayu-light")  # Markdown 排版样式
CODE_THEME = config_getter.get_config("config", "code_theme", fallback="kimbie-light")  # 代码高亮主题

if __name__ == '__main__':
    print()
    # 相关文件夹初始化
    if cp_utils.is_dir_existed(md_dir) or cp_utils.is_dir_existed(out_dir):
        print("目录不存在")
        exit(0)
    
    # 文件检查
    md_file_path_list = cp_utils.filter_file_type(md_dir, '.md')
    if len(md_file_path_list) == 0:
        print("当前目录无md文件，请检查后重试！" + md_dir)
        exit(0)
    
    # 检查并启动 bm.md 服务
    if not is_service_running():
        print("无法连接到 bm.md 服务，请确保服务已启动后重试")
        exit(0)
    
    print("begin sync to wechat")
    start_time = time.time()  # 开始时间
    sync.init_cache()
    client, token = sync.Client()
    
    for md_file_path in md_file_path_list:
        split_list = md_file_path.split(os.sep)
        if len(split_list) > 0:
            file_name = split_list[-1]
            print("读取文件 →", file_name)
            file_content = cp_utils.read_file_content(md_file_path)
            ## 图片资源上传微信公众号
            file_content, imageId = sync.update_images_urls(file_content, client)
            ## 获取文章基础信息
            baseinfo = sync.BaseInfo(file_content, imageId, md_file_path)
            
            print(f"应用样式 → {MARKDOWN_STYLE}, 代码主题 → {CODE_THEME}")
            renderer_content = render_article(file_content, MARKDOWN_STYLE, CODE_THEME)
            
            if not renderer_content:
                print(f"渲染失败: {file_name}")
                continue
            
            out_file_path = os.path.join(out_dir, file_name.replace(".md", ".html"))
            print("输出文件 →", out_file_path)
            cp_utils.write_file(renderer_content, out_file_path)
            
            # if sync.upload_media_news(renderer_content, baseinfo, token):
            #     sync.cache_update(md_file_path)
            #     print("sync " + md_file_path + " to wechat successful")
