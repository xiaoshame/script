# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""
-------------------------------------------------
   File     : bm_md_renderer.py
   Author   : Generated
   date     : 2026-01-20
   Desc     : 使用 bm.md 服务进行 Markdown 转 HTML 渲染
-------------------------------------------------
"""
import os
import subprocess
import time
import requests
import atexit
import signal
import sync

# bm.md 服务配置
BM_MD_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bm.md')
# 使用官方 bm.md API 服务
BM_MD_API_URL = "https://bm.md/api/markdown/render"
# 本地开发服务器 URL (备用)
# BM_MD_API_URL = "http://localhost:2663/api/markdown/render"
BM_MD_PROCESS = None

# 可用的 Markdown 样式
MARKDOWN_STYLES = [
    'ayu-light', 'bauhaus', 'blueprint', 'botanical', 'green-simple',
    'maximalism', 'neo-brutalism', 'newsprint', 'organic', 
    'playful-geometric', 'professional', 'retro', 'sketch', 'terminal'
]

# 可用的代码主题
CODE_THEMES = [
    'catppuccin-frappe', 'catppuccin-latte', 'catppuccin-macchiato', 
    'catppuccin-mocha', 'kimbie-dark', 'kimbie-light', 'panda-syntax-dark',
    'panda-syntax-light', 'paraiso-dark', 'paraiso-light', 'rose-pine',
    'rose-pine-dawn', 'tokyo-night-dark', 'tokyo-night-light'
]


def is_service_running():
    """检查 bm.md 服务是否可用"""
    try:
        # 发送一个简单的测试请求
        response = requests.post(
            BM_MD_API_URL,
            json={"markdown": "test"},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        return response.status_code == 200
    except:
        return False


def render_markdown(
    markdown_content: str,
    markdown_style: str = 'ayu-light',
    code_theme: str = 'kimbie-light',
    custom_css: str = '',
    enable_footnote_links: bool = True,
    open_links_in_new_window: bool = True,
    platform: str = 'wechat',
    footnote_label: str = 'Footnotes',
    reference_title: str = 'References'
) -> str:
    """
    使用 bm.md 服务渲染 Markdown 为 HTML
    
    :param markdown_content: Markdown 源文本
    :param markdown_style: Markdown 排版样式 ID
    :param code_theme: 代码块高亮主题 ID
    :param custom_css: 自定义 CSS 样式
    :param enable_footnote_links: 是否将文中链接自动转换为脚注形式
    :param open_links_in_new_window: 是否为所有外部链接添加 target="_blank"
    :param platform: 目标发布平台 (html, wechat, zhihu, juejin)
    :param footnote_label: GFM 脚注区域标题
    :param reference_title: 外部链接参考区域标题
    :return: 渲染后的 HTML 片段
    """
    
    # 验证样式参数
    if markdown_style not in MARKDOWN_STYLES:
        print(f"警告: 未知的 markdown_style '{markdown_style}', 使用默认值 'ayu-light'")
        markdown_style = 'ayu-light'
    
    if code_theme not in CODE_THEMES:
        print(f"警告: 未知的 code_theme '{code_theme}', 使用默认值 'kimbie-light'")
        code_theme = 'kimbie-light'
    
    # 构建请求数据
    payload = {
        "markdown": markdown_content,
        "markdownStyle": markdown_style,
        "codeTheme": code_theme,
        "customCss": custom_css,
        "enableFootnoteLinks": enable_footnote_links,
        "openLinksInNewWindow": open_links_in_new_window,
        "platform": platform,
        "footnoteLabel": footnote_label,
        "referenceTitle": reference_title
    }
    
    try:
        response = requests.post(
            BM_MD_API_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('result', '')
        else:
            print(f"API 请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return ''
            
    except requests.exceptions.ConnectionError:
        print("无法连接到 bm.md 服务，请确保服务已启动")
        return ''
    except Exception as e:
        print(f"渲染 Markdown 时发生错误: {e}")
        return ''


def render_article(content: str, markdown_style: str = 'ayu-light', code_theme: str = 'kimbie-light') -> str:
    """
    渲染文章（兼容原有接口）
    
    :param content: Markdown 内容
    :param markdown_style: Markdown 排版样式
    :param code_theme: 代码高亮主题
    :return: 渲染后带样式的 HTML 内容
    """
    # 去掉 YAML front matter
    if content.startswith('---'):
        parts = content.split('---\n', 2)
        if len(parts) >= 3:
            content = parts[2]
    
    html_content = render_markdown(
        markdown_content=content,
        markdown_style=markdown_style,
        code_theme=code_theme,
        platform='wechat'
    )
    
    # 应用额外的样式美化处理（链接转换、添加头尾等）
    if html_content:
        html_content = sync.css_beautify(html_content)
    
    return html_content


if __name__ == '__main__':
    # 测试代码
    test_md = """
# 测试标题

这是一段测试文本。

## 二级标题

- 列表项 1
- 列表项 2

```python
def hello():
    print("Hello, World!")
```

> 这是一段引用

**粗体文本** 和 *斜体文本*
"""
    
    # 确保服务运行
    if not is_service_running():
        print("bm.md 服务未运行，无法进行测试")
    
    if is_service_running():
        result = render_markdown(test_md)
        print(result)
    else:
        print("服务未能启动")
