"""
泰坦之旅百科 - Flask Web 应用
支持浏览、搜索 CHM 解压后的游戏百科资料
"""

import os
import re
import json
import html
import gzip
import hashlib
from io import BytesIO
from pathlib import Path
from collections import defaultdict
from flask import Flask, request, jsonify, send_from_directory, render_template, Response, abort

app = Flask(__name__)


# ========== Gzip 压缩 ==========
@app.after_request
def compress_response(response):
    """对大于 500 字节的文本响应进行 gzip 压缩"""
    if (
        response.status_code < 200
        or response.status_code >= 300
        or response.direct_passthrough
        or 'Content-Encoding' in response.headers
        or not response.content_type
    ):
        return response

    # 只压缩文本类型
    ct = response.content_type.lower()
    if not any(t in ct for t in ['text/', 'application/json', 'application/javascript', 'image/svg']):
        return response

    accept_enc = request.headers.get('Accept-Encoding', '')
    if 'gzip' not in accept_enc:
        return response

    data = response.get_data()
    if len(data) < 500:
        return response

    buf = BytesIO()
    with gzip.GzipFile(fileobj=buf, mode='wb', compresslevel=6) as gz:
        gz.write(data)
    compressed = buf.getvalue()

    # 只在压缩确实更小时使用
    if len(compressed) < len(data):
        response.set_data(compressed)
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Content-Length'] = len(compressed)
        response.headers['Vary'] = 'Accept-Encoding'

    # 保持连接活跃，减少移动端超时
    response.headers['Connection'] = 'keep-alive'
    response.headers['Keep-Alive'] = 'timeout=30'

    return response


# ========== 配置 ==========
BASE_DIR = Path(__file__).parent.resolve()

# 数据源定义
SOURCES = [
    {
        "key": "wiki",
        "name": "百科全书",
        "icon": "📖",
        "dir": BASE_DIR / "chm_extracted",
        "encoding": "gb2312",
        "description": "泰坦百科JOYGAO豪华图片版 - 职业、技能、装备、怪物等",
    },
    {
        "key": "equip",
        "name": "装备数据库",
        "icon": "⚔️",
        "dir": BASE_DIR / "chm_equip",
        "encoding": "gbk",
        "description": "装备详细数据 - 武器、护甲、饰品、套装、技能等",
    },
    {
        "key": "guide",
        "name": "攻略地图",
        "icon": "🗺️",
        "dir": BASE_DIR / "chm_guide",
        "encoding": "gb2312",
        "description": "任务攻略文字版与地图版",
    },
]

SOURCE_MAP = {s["key"]: s for s in SOURCES}

# ========== 搜索索引 ==========
search_index = []  # [{source, path, title, text, category}]
index_built = False


def strip_html_tags(html_str):
    """移除 HTML 标签，保留纯文本"""
    text = re.sub(r'<script[^>]*>.*?</script>', '', html_str, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def read_file_content(filepath, encoding="gb2312"):
    """尝试读取文件内容，自动处理编码问题"""
    try:
        with open(filepath, "rb") as f:
            raw = f.read()
    except IOError:
        return ""

    # 从 meta charset 标签检测编码
    meta_enc = None
    m = re.search(rb'charset[="\s]+([a-zA-Z0-9_-]+)', raw[:2000], re.IGNORECASE)
    if m:
        meta_enc = m.group(1).decode('ascii', errors='ignore').strip('"\'= ')

    # 构建尝试列表（优先用 meta 声明的编码）
    encodings = []
    if meta_enc:
        encodings.append(meta_enc)
    encodings.extend([encoding, "utf-8", "gbk", "gb18030", "latin-1"])

    # 去重
    seen = set()
    unique = []
    for e in encodings:
        key = e.lower().replace("-", "").replace("_", "")
        if key not in seen:
            seen.add(key)
            unique.append(e)

    for enc in unique:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue

    return raw.decode("utf-8", errors="replace")


def extract_title_from_html(content):
    """从 HTML 中提取 <title> 标签内容"""
    m = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    if m:
        title = strip_html_tags(m.group(1)).strip()
        if title and len(title) < 200:
            return title
    return ""


def get_category_from_path(filepath, source_dir):
    """根据文件路径推算分类"""
    rel = os.path.relpath(filepath, source_dir)
    parts = Path(rel).parts
    if len(parts) > 1:
        return parts[0]
    return "根目录"


def build_search_index():
    """构建全文搜索索引"""
    global search_index, index_built
    if index_built:
        return

    print("正在构建搜索索引...")
    search_index = []

    for src in SOURCES:
        source_dir = src["dir"]
        if not source_dir.exists():
            continue

        count = 0
        for root, dirs, files in os.walk(source_dir):
            # 跳过图片等资源目录
            dirs[:] = [d for d in dirs if d not in ("graphics", "Preface_files", "Index_files",
                                                      "Map_files", "Text_files")]
            for fname in files:
                if not fname.lower().endswith((".htm", ".html")):
                    continue
                # 跳过目录索引文件和框架页
                if fname.lower() in ("toc.html", "index.html") and src["key"] != "guide":
                    if "Equipments" not in root and "Prefixes" not in root:
                        continue

                filepath = os.path.join(root, fname)
                rel_path = os.path.relpath(filepath, source_dir).replace("\\", "/")

                content = read_file_content(filepath, src["encoding"])
                if not content:
                    continue

                title = extract_title_from_html(content)
                if not title:
                    # 用文件名作为标题
                    title = Path(fname).stem

                plain_text = strip_html_tags(content)
                if len(plain_text) < 10:
                    continue

                category = get_category_from_path(filepath, source_dir)

                search_index.append({
                    "source": src["key"],
                    "sourceName": src["name"],
                    "path": rel_path,
                    "title": title,
                    "text": plain_text[:3000],  # 限制索引文本长度
                    "category": category,
                })
                count += 1

        print(f"  [{src['name']}] 索引了 {count} 个页面")

    index_built = True
    print(f"搜索索引构建完成，共 {len(search_index)} 条记录")


# ========== 目录树构建 ==========

# 百科全书 - 按照合理的分类顺序手动定义
WIKI_TOC_ORDER = [
    "泰坦百科JOYGAO",
    "泰坦之旅职业",
    "技能",
    "装备",
    "怪物",
    "TQ全职业攻略",
    "TQ数据详解",
    "TQ解析心得",
    "TQIT神器配方集",
    "泰坦主副线任务攻略",
    "泰坦之旅任务图电子书",
    "数据总表",
    "神坛效果说明",
    "恶搞物品全集",
    "泰坦之旅开启隐藏内容密码",
    "泰坦之旅掉宝mod制作指南",
    "泰坦之旅游戏模组制作指南",
    "泰坦设置文件优化方法",
    "直接解压泰坦之旅音乐",
    "BUG汇总",
]

# 装备数据库 - 分类索引页映射
EQUIP_INDEX_PAGES = [
    {"name": "📋 目录总览", "path": "toc.html"},
    {"name": "🗡️ 剑", "path": "index_swords.html"},
    {"name": "🪓 斧", "path": "index_axes.html"},
    {"name": "🔨 锤", "path": "index_clubs.html"},
    {"name": "🏹 弓", "path": "index_bows.html"},
    {"name": "🔱 矛", "path": "index_spears.html"},
    {"name": "🪄 法杖", "path": "index_staffs.html"},
    {"name": "🛡️ 盾", "path": "index_shields.html"},
    {"name": "⛑️ 头盔", "path": "index_helms.html"},
    {"name": "🦺 胸甲", "path": "index_torsos.html"},
    {"name": "🥾 护腿", "path": "index_greaves.html"},
    {"name": "🧤 臂甲", "path": "index_armbands.html"},
    {"name": "💍 戒指", "path": "index_rings.html"},
    {"name": "📿 项链", "path": "index_amulets.html"},
    {"name": "🎯 投掷", "path": "index_throwings.html"},
    {"name": "⭐ 神器", "path": "index_artifacts.html"},
    {"name": "🧿 遗物", "path": "index_relics.html"},
    {"name": "🔮 符咒", "path": "index_charms.html"},
    {"name": "📜 卷轴", "path": "index_scrolls.html"},
    {"name": "🎒 杂项", "path": "index_miscellaneous.html"},
    {"name": "🏅 套装", "path": "index_sets.html"},
    {"name": "⚡ 技能", "path": "index_skills.html"},
    {"name": "🔰 前缀", "path": "index_prefixes.html"},
    {"name": "🔰 后缀", "path": "index_suffixes.html"},
    {"name": "🐉 Boss怪物", "path": "index_creatures_boss.html"},
    {"name": "👹 普通怪物", "path": "index_creatures_common.html"},
    {"name": "📦 容器", "path": "index_containers.html"},
    {"name": "📋 任务", "path": "index_quests.html"},
]


def build_wiki_toc():
    """构建百科全书的目录树"""
    source_dir = SOURCE_MAP["wiki"]["dir"]
    if not source_dir.exists():
        return []

    toc = []
    seen_dirs = set()

    # 先按定义顺序处理
    for dirname in WIKI_TOC_ORDER:
        dirpath = source_dir / dirname
        if dirpath.exists() and dirpath.is_dir():
            seen_dirs.add(dirname)
            node = build_dir_tree(dirpath, source_dir, SOURCE_MAP["wiki"]["encoding"])
            if node:
                toc.append(node)

    # 补充未列出的目录
    for item in sorted(source_dir.iterdir()):
        if item.is_dir() and item.name not in seen_dirs:
            node = build_dir_tree(item, source_dir, SOURCE_MAP["wiki"]["encoding"])
            if node:
                toc.append(node)

    return toc


def build_dir_tree(dirpath, source_dir, encoding):
    """递归构建目录树节点"""
    dirname = dirpath.name
    node = {"name": dirname, "children": []}

    # 收集子目录
    subdirs = []
    files = []

    for item in sorted(dirpath.iterdir()):
        if item.is_dir():
            # 跳过资源目录
            if item.name in ("Preface_files", "Index_files", "Map_files", "Text_files",
                             "graphics", "Unused"):
                continue
            subdirs.append(item)
        elif item.suffix.lower() in (".htm", ".html"):
            # 跳过非内容文件
            if item.name.lower() in ("toc.html",):
                continue
            files.append(item)

    # 如果只有一个 htm 文件且没有子目录，直接作为叶子节点
    if len(files) == 1 and not subdirs:
        rel = os.path.relpath(files[0], source_dir).replace("\\", "/")
        node["path"] = rel
        return node

    # 先添加当前目录的 htm 文件
    for f in files:
        rel = os.path.relpath(f, source_dir).replace("\\", "/")
        fname = f.stem
        # 使用文件名作为显示名称（避免读取每个文件的title，提升性能）
        child = {"name": fname, "path": rel}
        node["children"].append(child)

    # 递归添加子目录
    for sd in subdirs:
        child_node = build_dir_tree(sd, source_dir, encoding)
        if child_node:
            node["children"].append(child_node)

    # 如果目录下什么内容都没有，返回None
    if not node["children"] and "path" not in node:
        return None

    return node


def build_equip_toc():
    """构建装备数据库的目录树"""
    toc = []
    source_dir = SOURCE_MAP["equip"]["dir"]

    for item in EQUIP_INDEX_PAGES:
        filepath = source_dir / item["path"]
        if filepath.exists():
            toc.append({"name": item["name"], "path": item["path"]})

    # 添加 Equipments 下的装备分类文件
    equip_dir = source_dir / "Equipments"
    if equip_dir.exists():
        equip_node = {"name": "📦 装备详情页", "children": []}

        # 按类型分组
        type_groups = defaultdict(list)
        for f in sorted(equip_dir.iterdir()):
            if f.suffix.lower() == ".html" and "_toc" not in f.name and "_main" not in f.name:
                # 提取类型前缀
                name = f.stem
                if name.startswith("Weapon") or name.startswith("Armor") or name.startswith("Item"):
                    type_groups["装备类型"].append(f)
                elif name.startswith("tagSet"):
                    type_groups["套装"].append(f)
                elif name.startswith("tagSkill") or name.startswith("xtagSkill"):
                    type_groups["技能"].append(f)
                # 其他类型不在目录中直接列出，但可以通过搜索找到

        for group_name, group_files in type_groups.items():
            group_node = {"name": group_name, "children": []}
            for f in group_files[:30]:  # 限制每组显示数量
                rel = os.path.relpath(f, source_dir).replace("\\", "/")
                group_node["children"].append({"name": f.stem, "path": rel})
            if len(group_files) > 30:
                group_node["children"].append({"name": f"... 还有 {len(group_files) - 30} 个", "path": ""})
            equip_node["children"].append(group_node)

        if equip_node["children"]:
            toc.append(equip_node)

    return toc


def build_guide_toc():
    """构建攻略地图的目录树"""
    source_dir = SOURCE_MAP["guide"]["dir"]
    toc = []

    # 文字攻略
    text_node = {"name": "📝 文字攻略", "children": []}
    text_files = [
        ("攻略索引", "text_index.htm"),
        ("第一章", "text_01.htm"),
        ("第二章", "text_02.htm"),
        ("第三章", "text_03.htm"),
        ("第四章", "text_04.htm"),
        ("第五章", "text_05.htm"),
        ("第六章", "text_06.htm"),
        ("第七章", "text_07.htm"),
        ("第八章", "text_08.htm"),
    ]
    for name, filename in text_files:
        filepath = source_dir / filename
        if filepath.exists():
            text_node["children"].append({"name": name, "path": filename})
    if text_node["children"]:
        toc.append(text_node)

    # 地图
    map_node = {"name": "🗺️ 地图攻略", "children": []}
    map_files = [
        ("地图索引", "map_index.htm"),
        ("第一章地图", "map_01.htm"),
        ("第二章地图", "map_02.htm"),
        ("第三章地图", "map_03.htm"),
        ("第四章地图", "map_04.htm"),
        ("第五章地图", "map_05.htm"),
        ("第六章地图", "map_06.htm"),
        ("第八章地图", "map_08.htm"),
    ]
    for name, filename in map_files:
        filepath = source_dir / filename
        if filepath.exists():
            map_node["children"].append({"name": name, "path": filename})
    if map_node["children"]:
        toc.append(map_node)

    # 前言
    preface = source_dir / "preface.htm"
    if preface.exists():
        toc.insert(0, {"name": "📋 前言", "path": "preface.htm"})

    return toc


# 缓存目录树
_toc_cache = {}


def get_toc(source_key):
    if source_key in _toc_cache:
        return _toc_cache[source_key]

    if source_key == "wiki":
        toc = build_wiki_toc()
    elif source_key == "equip":
        toc = build_equip_toc()
    elif source_key == "guide":
        toc = build_guide_toc()
    else:
        toc = []

    _toc_cache[source_key] = toc
    return toc


# ========== HTML 页面处理 ==========

def process_html_for_iframe(content, source_key, file_path):
    """处理 HTML 内容，使其适合在 iframe 中展示"""

    # 1. 确保使用 UTF-8 编码声明
    content = re.sub(
        r'<meta[^>]*charset[^>]*>',
        '<meta charset="utf-8">',
        content,
        flags=re.IGNORECASE
    )
    content = re.sub(
        r'<meta[^>]*Content-Type[^>]*>',
        '<meta http-equiv="Content-Type" content="text/html; charset=utf-8">',
        content,
        flags=re.IGNORECASE
    )

    # 2. 计算当前文件所在目录的相对路径
    src = SOURCE_MAP[source_key]
    source_dir = str(src["dir"]).replace("\\", "/")
    file_dir = os.path.dirname(file_path).replace("\\", "/")
    rel_dir = os.path.relpath(file_dir, source_dir).replace("\\", "/")
    if rel_dir == ".":
        rel_dir = ""

    # 3. 修复资源路径（图片、CSS 等）
    def fix_resource_url(match):
        tag = match.group(0)
        attr_name = match.group(1)  # src or href or background
        url = match.group(2)

        # 跳过绝对URL、锚点、JavaScript、data URI
        if url.startswith(("http://", "https://", "//", "#", "javascript:", "data:", "mailto:")):
            return tag

        # 跳过内联 CSS 和 JS 的 href
        if 'stylesheet' not in tag.lower() and attr_name.lower() == 'href' and not url.endswith(('.htm', '.html', '.css')):
            # 可能是 htm/html 的链接，需要转换
            pass

        # 对于 .htm/.html 链接，转换为通过 API 加载
        if url.lower().endswith(('.htm', '.html')):
            # 去掉锚点部分
            anchor = ""
            if "#" in url:
                url, anchor = url.rsplit("#", 1)

            # 计算完整路径
            if url.startswith("/"):
                full_path = url.lstrip("/")
            else:
                if rel_dir:
                    full_path = os.path.normpath(os.path.join(rel_dir, url)).replace("\\", "/")
                else:
                    full_path = url

            if attr_name.lower() == "src" and ("frame" in tag.lower()):
                # iframe/frame 的 src，直接指向 API
                return tag.replace(match.group(2), f"/api/page/{source_key}?path={full_path}")

            # 普通链接，通过 postMessage 通知父窗口
            if attr_name.lower() == "href":
                anchor_str = f', &quot;anchor&quot;: &quot;{anchor}&quot;' if anchor else ""
                onclick = f'event.preventDefault(); window.parent.postMessage({{&quot;type&quot;: &quot;loadPage&quot;, &quot;source&quot;: &quot;{source_key}&quot;, &quot;path&quot;: &quot;{full_path}&quot;{anchor_str}}}, &quot;*&quot;)'
                return tag.replace(f'href="{match.group(2)}"', f'href="#" onclick="{onclick}"')
            return tag

        # 静态资源（CSS/图片等），指向文件服务
        if url.startswith("/"):
            res_path = url.lstrip('/')
        elif rel_dir:
            res_path = os.path.normpath(os.path.join(rel_dir, url)).replace('\\', '/')
        else:
            res_path = url
        new_url = f"/static_res/{source_key}/{res_path}"

        return tag.replace(match.group(2), new_url)

    # 匹配 src="..." href="..." background="..."
    content = re.sub(
        r'(src|href|background)\s*=\s*"([^"]*)"',
        fix_resource_url,
        content,
        flags=re.IGNORECASE
    )
    # 匹配单引号版本
    content = re.sub(
        r"(src|href|background)\s*=\s*'([^']*)'",
        fix_resource_url,
        content,
        flags=re.IGNORECASE
    )

    # 4. 注入基础样式改善阅读体验
    inject_style = """
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=3.0">
<style>
    body {
        max-width: 100% !important;
        overflow-x: hidden !important;
        padding: 8px !important;
        font-family: "Microsoft YaHei", "PingFang SC", sans-serif !important;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    img { max-width: 100%; height: auto; }
    table { max-width: 100%; }
    pre { overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; }
    @media (max-width: 768px) {
        body { padding: 4px !important; font-size: 14px !important; }
        /* 装备详情表格：纵向堆叠 */
        table[width], table[border] {
            width: 100% !important;
            display: table !important;
            table-layout: fixed !important;
        }
        td, th {
            word-wrap: break-word;
            overflow-wrap: break-word;
            max-width: 0;
        }
        /* 装备属性内嵌表格横向滚动 */
        td > table, td > div > table {
            table-layout: auto !important;
            display: block !important;
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch;
            max-width: 100% !important;
        }
        /* 掉落列表横向滚动 */
        .longtable {
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch;
        }
        .longtable table {
            table-layout: auto !important;
            min-width: 500px;
        }
        img { max-width: 100% !important; height: auto !important; }
        /* 固定宽度的旧式布局表格 */
        table[width="942"], table[width="1280"] {
            width: 100% !important;
        }
        td[width], th[width] {
            width: auto !important;
        }
    }
</style>
"""
    if '</head>' in content.lower():
        content = re.sub(r'(</head>)', inject_style + r'\1', content, count=1, flags=re.IGNORECASE)
    else:
        content = inject_style + content

    # 5. 给所有图片加懒加载，避免一次性发起大量请求
    content = re.sub(
        r'<img(?![^>]*loading=)',
        '<img loading="lazy" decoding="async"',
        content, flags=re.IGNORECASE
    )

    return content


# ========== Frameset 处理 ==========

def handle_frameset_page(content, source_key, file_path):
    """处理 frameset 页面，将嵌套 frame 合并为单页展示"""
    src = SOURCE_MAP[source_key]
    source_dir = str(src["dir"])
    file_dir = os.path.dirname(file_path)

    # 解析所有 frame
    frames = []
    for m in re.finditer(r'<frame([^>]*)>', content, re.IGNORECASE):
        attrs = m.group(1)
        src_m = re.search(r'src\s*=\s*["\']([^"\']+)["\']', attrs, re.IGNORECASE)
        name_m = re.search(r'name\s*=\s*["\']([^"\']+)["\']', attrs, re.IGNORECASE)
        if src_m:
            frame_src = src_m.group(1)
            frame_name = name_m.group(1) if name_m else ""
            abs_path = os.path.normpath(os.path.join(file_dir, frame_src))
            rel_path = os.path.relpath(abs_path, source_dir).replace("\\", "/")
            frames.append({
                "src": frame_src,
                "name": frame_name,
                "rel_path": rel_path,
                "abs_path": abs_path,
            })

    if not frames:
        return None

    # 检测布局类型
    frameset_match = re.search(r'<frameset[^>]*\s(cols|rows)\s*=', content, re.IGNORECASE)
    layout = frameset_match.group(1).lower() if frameset_match else "rows"

    if layout == "rows":
        # Rows 布局（如 index_swords.html）：跳过顶部导航栏，加载主内容
        main_frame = frames[-1]
        if not os.path.isfile(main_frame["abs_path"]):
            return None
        target_content = read_file_content(main_frame["abs_path"], src["encoding"])
        if not target_content:
            return None
        # 目标也是 frameset 则递归处理
        if '<frameset' in target_content.lower():
            return handle_frameset_page(target_content, source_key, main_frame["abs_path"])
        processed = process_html_for_iframe(target_content, source_key, main_frame["abs_path"])
        return Response(processed, content_type="text/html; charset=utf-8")

    elif layout == "cols":
        # Cols 布局（如 WeaponMelee_Sword.html）：构建双栏页面
        return _build_combined_equip_page(frames, source_key, source_dir)

    return None


def _build_combined_equip_page(frames, source_key, source_dir):
    """将 cols frameset 的 TOC 和主内容合并为响应式双栏页面"""
    src = SOURCE_MAP[source_key]
    toc_frame = frames[0]
    main_frame = frames[1] if len(frames) > 1 else frames[0]

    # 读取内容
    toc_raw = read_file_content(toc_frame["abs_path"], src["encoding"]) or ""
    main_raw = read_file_content(main_frame["abs_path"], src["encoding"]) or ""

    # 判断两个 frame 是否指向同一文件（如 sets.html）
    same_source = (os.path.normpath(toc_frame["abs_path"])
                   == os.path.normpath(main_frame["abs_path"]))

    # ---- 提取 CSS 引用 ----
    def get_css_tags(raw_html, file_abs_path):
        tags = []
        for cm in re.finditer(r'<link[^>]+href="([^"]+\.css)"[^>]*>', raw_html, re.IGNORECASE):
            css_href = cm.group(1)
            if css_href.startswith(('http://', 'https://')):
                tags.append(f'<link rel="stylesheet" href="{css_href}">')
            else:
                css_abs = os.path.normpath(
                    os.path.join(os.path.dirname(file_abs_path), css_href))
                css_rel = os.path.relpath(css_abs, source_dir).replace("\\", "/")
                tags.append(f'<link rel="stylesheet" href="/static_res/{source_key}/{css_rel}">')
        return tags

    css_set = set(get_css_tags(toc_raw, toc_frame["abs_path"]))
    if not same_source:
        css_set.update(get_css_tags(main_raw, main_frame["abs_path"]))
    css_tags = "\n".join(css_set)

    # ---- 提取 body 内容 ----
    def extract_body(html):
        bm = re.search(r'<body[^>]*>(.*)</body>', html, re.IGNORECASE | re.DOTALL)
        if bm:
            return bm.group(1)
        idx = html.lower().find('</head>')
        if idx >= 0:
            return html[idx + 7:]
        return html

    toc_body = extract_body(toc_raw)
    main_body = extract_body(main_raw) if not same_source else ""

    # ---- 通用：修复资源 URL ----
    def fix_res(match, file_abs_path):
        attr, url = match.group(1), match.group(2)
        if url.startswith(('http://', 'https://', '//', '#', 'javascript:', 'data:')):
            return match.group(0)
        res_abs = os.path.normpath(os.path.join(os.path.dirname(file_abs_path), url))
        res_rel = os.path.relpath(res_abs, source_dir).replace("\\", "/")
        return f'{attr}="/static_res/{source_key}/{res_rel}"'

    # 修复 TOC 中的图片等资源
    toc_body = re.sub(
        r'(src|background)\s*=\s*"([^"]*)"',
        lambda m: fix_res(m, toc_frame["abs_path"]),
        toc_body, flags=re.IGNORECASE
    )
    # TOC 图片懒加载
    toc_body = re.sub(
        r'<img(?![^>]*loading=)',
        '<img loading="lazy" decoding="async"',
        toc_body, flags=re.IGNORECASE
    )

    # ---- 修复 TOC 链接 ----
    toc_dir = os.path.dirname(toc_frame["abs_path"]).replace("\\", "/")

    def fix_toc_href(match):
        href = match.group(1)
        if href.startswith(('javascript:', 'http://', 'https://', 'data:')):
            return match.group(0)
        if href.startswith('#'):
            # 锚点链接 → 改为 data-anchor，由 JS 在 iframe 内滚动
            anchor = href[1:]
            return f'href="#" data-anchor="{anchor}"'
        # 不含锚点 或 同源模式 → 数据属性，由 JS 加载到右侧面板
        url_part = href.split('#')[0] if '#' in href else href
        anchor_part = href.rsplit('#', 1)[1] if '#' in href else ''
        full_abs = os.path.normpath(os.path.join(toc_dir, url_part))
        full_rel = os.path.relpath(full_abs, source_dir).replace("\\", "/")
        return f'href="#" data-page="{full_rel}" data-anchor="{anchor_part}"'

    toc_body = re.sub(r'href="([^"]*)"', fix_toc_href, toc_body, flags=re.IGNORECASE)
    toc_body = re.sub(r'\s+target="[^"]*"', '', toc_body, flags=re.IGNORECASE)

    if main_body:
        # 主内容不再内联，通过 iframe 加载，无需处理链接和资源
        pass

    # ---- 特殊情况：主内容为空（非同源情况仍保留双栏） ----
    if not same_source and not main_raw.strip():
        processed = process_html_for_iframe(toc_raw, source_key, toc_frame["abs_path"])
        return Response(processed, content_type="text/html; charset=utf-8")

    # 统一使用 iframe 加载主内容，避免移动端 DOM 过多导致崩溃
    if same_source:
        # 同源 (如 quests.html)：右侧初始为空，TOC 点击后加载
        iframe_initial_src = "about:blank"
        show_placeholder = True
    else:
        # 非同源 (如 WeaponMelee_Sword.html)：右侧直接加载主内容
        main_rel = os.path.relpath(main_frame["abs_path"], source_dir).replace("\\", "/")
        iframe_initial_src = f"/api/page/{source_key}?path={main_rel}"
        show_placeholder = False

    right_panel = f'<iframe id="equip-detail-frame" src="{iframe_initial_src}" style="width:100%;height:100%;border:none;"></iframe>'

    # ---- 构建双栏组合页面 ----
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=3.0">
{css_tags}
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ display: flex; height: 100vh; font-family: "Microsoft YaHei", sans-serif; overflow: hidden; }}
#equip-toc {{
    width: 260px; min-width: 180px; overflow-y: auto;
    border-right: 2px solid #e0e0e0; background: #fafafa;
    padding: 8px; flex-shrink: 0;
}}
#equip-toc p {{ margin: 1px 0; }}
#equip-toc a {{
    color: #333; text-decoration: none; display: block;
    padding: 3px 8px; border-radius: 4px; font-size: 13px; line-height: 1.4;
}}
#equip-toc a:hover {{ background: #e0e7ff; color: #1a73e8; }}
#equip-toc a.active {{ background: #c8d6ff; color: #0d47a1; font-weight: bold; }}
#equip-main {{
    flex: 1; overflow: hidden; padding: 0;
}}
#toc-toggle {{
    display: none; position: fixed; bottom: 20px; left: 20px; z-index: 200;
    width: 44px; height: 44px; border-radius: 50%;
    background: #1a73e8; color: #fff; border: none;
    font-size: 20px; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    line-height: 44px; text-align: center;
}}
#toc-overlay {{
    display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 99;
}}
#toc-overlay.show {{ display: block; }}
.equip-placeholder {{
    display: flex; align-items: center; justify-content: center;
    height: 100%; color: #aaa; font-size: 16px;
}}
@media (max-width: 768px) {{
    body {{ flex-direction: column; }}
    #equip-toc {{
        position: fixed; left: 0; top: 0; bottom: 0; z-index: 100;
        transform: translateX(-100%); transition: transform 0.3s ease;
        box-shadow: 2px 0 10px rgba(0,0,0,0.2); width: 80vw; max-width: 300px;
        background: #fff;
    }}
    #equip-toc.open {{ transform: translateX(0); }}
    #equip-toc a {{ padding: 8px 10px; font-size: 15px; min-height: 38px; line-height: 1.5; }}
    #toc-toggle {{ display: block; }}
    #equip-main {{ width: 100%; overflow: hidden; }}
}}
</style></head>
<body>
<div id="toc-overlay" onclick="closeToc()"></div>
<div id="equip-toc">{toc_body}</div>
<div id="equip-main">{'<div class="equip-placeholder">\u2190 \u8bf7\u4ece\u5de6\u4fa7\u5217\u8868\u9009\u62e9\u67e5\u770b</div>' if show_placeholder else ''}{right_panel}</div>
<button id="toc-toggle" onclick="toggleToc()">\u2630</button>
<script>
var SAME_SOURCE = {'true' if same_source else 'false'};
var SOURCE_KEY = '{source_key}';
var MAIN_LOADED = {'false' if same_source else 'true'};

function toggleToc() {{
    document.getElementById('equip-toc').classList.toggle('open');
    document.getElementById('toc-overlay').classList.toggle('show');
}}
function closeToc() {{
    document.getElementById('equip-toc').classList.remove('open');
    document.getElementById('toc-overlay').classList.remove('show');
}}

document.getElementById('equip-toc').addEventListener('click', function(e) {{
    var link = e.target.closest('a');
    if (!link) return;
    e.preventDefault();

    var dataPage = link.getAttribute('data-page');
    var dataAnchor = link.getAttribute('data-anchor');

    // 高亮当前项
    document.querySelectorAll('#equip-toc a.active').forEach(function(a) {{ a.classList.remove('active'); }});
    link.classList.add('active');

    var frame = document.getElementById('equip-detail-frame');
    var placeholder = document.querySelector('.equip-placeholder');

    if (dataPage) {{
        // 有 data-page：加载新页面到 iframe
        if (placeholder) placeholder.style.display = 'none';
        frame.style.display = 'block';
        var url = '/api/page/' + SOURCE_KEY + '?path=' + encodeURIComponent(dataPage);
        if (dataAnchor) url += '#' + encodeURIComponent(dataAnchor);
        frame.src = url;
        MAIN_LOADED = true;
    }} else if (dataAnchor) {{
        // 只有锚点：在 iframe 内滚动到锚点位置
        if (frame && MAIN_LOADED) {{
            try {{
                var doc = frame.contentDocument || frame.contentWindow.document;
                var target = doc.getElementById(dataAnchor)
                    || doc.querySelector('[name="' + dataAnchor.replace(/"/g, '\\\\"') + '"]');
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }} catch(ex) {{
                // 降级为 hash 导航
                try {{ frame.contentWindow.location.hash = dataAnchor; }} catch(ex2) {{}}
            }}
        }}
    }}

    closeToc();
}});
</script>
</body></html>"""
    return Response(html, content_type="text/html; charset=utf-8")


# ========== Flask 路由 ==========

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/sources")
def api_sources():
    return jsonify([
        {"key": s["key"], "name": s["name"], "icon": s["icon"], "description": s["description"]}
        for s in SOURCES
    ])


@app.route("/api/toc/<source_key>")
def api_toc(source_key):
    if source_key not in SOURCE_MAP:
        return jsonify({"error": "未知数据源"}), 404
    return jsonify(get_toc(source_key))


@app.route("/api/page/<source_key>")
def api_page(source_key):
    if source_key not in SOURCE_MAP:
        abort(404)

    path = request.args.get("path", "")
    if not path:
        abort(400)

    # 安全检查
    path = path.replace("\\", "/")
    if ".." in path:
        abort(403)

    src = SOURCE_MAP[source_key]
    filepath = os.path.join(str(src["dir"]), path)
    filepath = os.path.normpath(filepath)

    # 确保路径在数据源目录内
    if not filepath.startswith(str(src["dir"])):
        abort(403)

    if not os.path.isfile(filepath):
        abort(404)

    content = read_file_content(filepath, src["encoding"])
    if not content:
        abort(500)

    # Frameset 页面特殊处理
    if '<frameset' in content.lower():
        resp = handle_frameset_page(content, source_key, filepath)
        if resp:
            return resp

    processed = process_html_for_iframe(content, source_key, filepath)
    return Response(processed, content_type="text/html; charset=utf-8")


@app.route("/static_res/<source_key>/<path:filepath>")
def static_resource(source_key, filepath):
    """提供静态资源文件（图片、CSS等）"""
    if source_key not in SOURCE_MAP:
        abort(404)

    src = SOURCE_MAP[source_key]

    # 路径规范化和安全检查
    filepath = os.path.normpath(filepath).replace("\\", "/")
    if ".." in filepath:
        abort(403)

    full_path = os.path.normpath(os.path.join(str(src["dir"]), filepath))
    if not full_path.startswith(str(src["dir"])):
        abort(403)

    if not os.path.isfile(full_path):
        abort(404)

    directory = os.path.dirname(full_path)
    filename = os.path.basename(full_path)

    # CSS 文件特殊处理编码
    if filename.lower().endswith('.css'):
        content = read_file_content(full_path, src["encoding"])
        resp = Response(content, content_type="text/css; charset=utf-8")
        resp.headers['Cache-Control'] = 'public, max-age=86400'
        return resp

    resp = send_from_directory(directory, filename)
    # 图片等静态资源缓存 1 天
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext in ('gif', 'jpg', 'jpeg', 'png', 'bmp', 'ico', 'svg', 'webp'):
        resp.headers['Cache-Control'] = 'public, max-age=86400'
    return resp


@app.route("/api/search")
def api_search():
    build_search_index()

    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])

    keywords = query.lower().split()
    results = []
    max_results = 100

    for entry in search_index:
        text_lower = entry["text"].lower()
        title_lower = entry["title"].lower()

        # 所有关键词都需要匹配（标题或文本）
        score = 0
        all_match = True
        for kw in keywords:
            in_title = kw in title_lower
            in_text = kw in text_lower
            if not in_title and not in_text:
                all_match = False
                break
            if in_title:
                score += 10  # 标题匹配加分
            if in_text:
                score += 1

        if not all_match:
            continue

        # 构建摘要片段
        snippet = ""
        for kw in keywords:
            idx = text_lower.find(kw)
            if idx >= 0:
                start = max(0, idx - 40)
                end = min(len(entry["text"]), idx + len(kw) + 80)
                snippet = ("..." if start > 0 else "") + entry["text"][start:end] + ("..." if end < len(entry["text"]) else "")
                break
        if not snippet:
            snippet = entry["text"][:120] + "..."

        results.append({
            "source": entry["source"],
            "sourceName": entry["sourceName"],
            "path": entry["path"],
            "title": entry["title"],
            "category": entry["category"],
            "snippet": snippet,
            "score": score,
        })

        if len(results) >= max_results * 3:
            break

    # 按分数排序
    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:max_results]

    # 移除 score 字段
    for r in results:
        del r["score"]

    return jsonify(results)


# ========== 启动 ==========
if __name__ == "__main__":
    print("=" * 50)
    print("  [TQ] 泰坦之旅百科 Web 服务")
    print("=" * 50)
    print(f"数据目录: {BASE_DIR}")
    print(f"数据源: {', '.join(s['name'] for s in SOURCES)}")
    print()

    # 后台构建索引（延迟到首次搜索时）
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
