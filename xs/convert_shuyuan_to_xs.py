# -*- coding: utf-8 -*-
"""阅读(legado) 书源 -> 香色(xiangse) 书源 转换器。

字段契约取自 xs1.json / xs2.json 实测：
  - POST 用 {"POST":true, "httpParams":{...}}，GET 的 httpParams 作 query 参数
  - "||" 是 "选择器||@js:后处理" 的管道符，不能用来表达 legado 的多选一
  - requestInfo 里 result 是上一步的 detailUrl 字符串，拿不到 HTML
  - 字段 XPath 一律以 // 开头，textNodes 对应 /text()
"""
import argparse
import json
import re
import sys
from urllib.parse import urljoin

try:
    from lxml import etree
except ImportError:
    etree = None


# ---------------------------------------------------------------- 规则解析

# legado 取值方式 -> XPath 后缀
VALUE_TOKENS = {
    "text": "",
    "html": "",
    "all": "",
    "textnodes": "/text()",
    "owntext": "/text()",
    "owetext": "/text()",  # legado 书源里常见的拼写错误
}
ATTR_TOKENS = {"href", "src", "content", "value", "title", "alt", "name", "id", "class"}


class Unsupported(Exception):
    """规则用到了香色无法表达的 legado 特性。"""


# 带这些片段的规则是 legado 自有语法，不能当 XPath/JSONPath 透传
LEGADO_HINT = re.compile(
    r"@(tag|class|id|text)\.|@(text|html|textNodes|ownText|href|src|content)\b", re.I
)


def parse_put_vars(init):
    """从 ruleBookInfo.init 的 @put:{k:"rule"} 里提取变量表。"""
    m = re.search(r"@put:\s*\{(.*)\}", init or "", re.S)
    if not m:
        return {}
    return dict(re.findall(r'(\w+)\s*:\s*"((?:[^"\\]|\\.)*)"', m.group(1)))


def expand_get(rule, variables):
    def sub(m):
        key = m.group(1)
        if key not in variables:
            raise Unsupported(f"@get:{{{key}}} 未在 init 中定义")
        return variables[key]

    return re.sub(r"@get:\{(\w+)\}", sub, rule)


def split_top(rule, sep):
    """按分隔符拆分，跳过 {} 内部的分隔符。"""
    parts, depth, i, start = [], 0, 0, 0
    while i < len(rule):
        if rule[i] == "{":
            depth += 1
        elif rule[i] == "}":
            depth -= 1
        elif depth == 0 and rule.startswith(sep, i):
            parts.append(rule[start:i])
            i += len(sep)
            start = i
            continue
        i += 1
    parts.append(rule[start:])
    return parts


def parse_regex_suffix(rule):
    """拆出 '规则##查找##替换' 中的正则清洗步骤，返回 (base, [(pattern, repl), ...])。"""
    segs = rule.split("##")
    base = segs[0]
    steps, i = [], 1
    while i < len(segs):
        pattern = segs[i]
        repl = segs[i + 1] if i + 1 < len(segs) else ""
        if pattern:
            steps.append((pattern, repl))
        i += 2
    return base, steps


def class_predicate(names):
    """精确的 class 匹配，避免 contains 把 s2x 也匹配进来。"""
    conds = [
        f'contains(concat(" ", normalize-space(@class), " "), " {n} ")' for n in names
    ]
    return "[" + " and ".join(conds) + "]"


def index_predicate(idx_list, exclude):
    conds = []
    for raw in idx_list:
        n = int(raw)
        if n >= 0:
            conds.append(f"position()={n + 1}")
        elif n == -1:
            conds.append("position()=last()")
        else:
            conds.append(f"position()=last(){n + 1}")
    joined = " or ".join(conds)
    return f"[not({joined})]" if exclude else f"[{joined}]"


def split_index(token):
    """从 'li!0:1' / 'p.1:2' / 'span.0' / 'a[-1]' 拆出 (名称, 索引谓词)。"""
    m = re.match(r"^(.*?)!(-?\d+(?::-?\d+)*)$", token)
    if m:
        return m.group(1), index_predicate(m.group(2).split(":"), exclude=True)
    m = re.match(r"^(.*?)\[(-?\d+)\]$", token)
    if m:
        return m.group(1), index_predicate([m.group(2)], exclude=False)
    m = re.match(r"^(.*?)\.(-?\d+(?::-?\d+)*)$", token)
    if m:
        return m.group(1), index_predicate(m.group(2).split(":"), exclude=False)
    return token, ""


def attr_selector(token):
    """[property="og:image"] / [property~=a|b] / [property$=name] -> XPath。"""
    token = token.replace("～", "~")  # 书源里常混入全角波浪号
    m = re.match(r'^\[([\w:.-]+)\s*([~$^*]?=)\s*"?([^"\]]*)"?\]$', token)
    if not m:
        return None
    attr, op, val = m.groups()
    if op == "=":
        return f'//*[@{attr}="{val}"]'
    if op == "~=":
        conds = " or ".join(f'contains(@{attr}, "{v}")' for v in val.split("|"))
        return f"//*[{conds}]"
    if op == "$=":
        return f'//*[substring(@{attr}, string-length(@{attr}) - {len(val) - 1}) = "{val}"]'
    if op == "^=":
        return f'//*[starts-with(@{attr}, "{val}")]'
    return f'//*[contains(@{attr}, "{val}")]'


def token_to_xpath(token):
    """把一个 legado 选择器片段转成 (节点路径, 索引谓词)。"""
    token = token.strip()
    if not token:
        return "", ""

    attr_xp = attr_selector(token)
    if attr_xp:
        return attr_xp, ""

    # class./id./tag. 前缀是 legado 自有语法，空格属于名字（多 class）
    if token.startswith("class."):
        name, pred = split_index(token[6:])
        return f"//*{class_predicate(name.split())}", pred
    if token.startswith("id."):
        name, pred = split_index(token[3:])
        return f'//*[@id="{name}"]', pred
    if token.startswith("tag."):
        name, pred = split_index(token[4:])
        return f"//{name}", pred
    if token.startswith("text."):
        return f'//*[contains(text(), "{token[5:]}")]', ""

    # 其余按 CSS 选择器处理，空格是后代组合子
    parts = token.split()
    path, pred = "", ""
    for i, part in enumerate(parts):
        name, p = split_index(part)
        if name.startswith("."):
            node = f"//*{class_predicate(name[1:].split('.'))}"
        elif name.startswith("#"):
            node = f'//*[@id="{name[1:]}"]'
        elif not name:
            node = "//*"
        else:
            m = re.match(r"^([\w-]+)([.#].+)?$", name)
            if not m:
                raise Unsupported(f"无法识别的选择器片段 {name!r}")
            tag, rest = m.group(1), m.group(2)
            node = f"//{tag}"
            if rest and rest.startswith("."):
                node += class_predicate(rest[1:].split("."))
            elif rest:
                node += f'[@id="{rest[1:]}"]'
        path += node
        if i == len(parts) - 1:
            pred = p
        elif p:
            path = f"({path}){p}"
    return path, pred


def rule_to_xpath(rule, item_tag="*"):
    """把单条(不含 || &&)的 legado 规则转成 XPath。

    item_tag 是列表项的标签名，用于 chapterName:"text" 这种只有取值、没有选择器的规则。
    """
    base, _ = parse_regex_suffix(rule)
    base = base.strip()
    if not base:
        return ""

    # legado 本身也支持 XPath / JSONPath，这类规则直接透传
    if base.startswith("@XPath:"):
        return base[7:]
    if base.startswith(("//", "/html", "$.")) and not LEGADO_HINT.search(base):
        return base
    if base.startswith("@CSS:"):
        base = base[5:]

    if "@js:" in base or "<js>" in base or "{{" in base:
        raise Unsupported("规则内含 JS 表达式")
    if "@get:" in base or "@put:" in base:
        raise Unsupported("规则使用 @put/@get 变量")

    tokens = [t for t in split_top(base, "@") if t.strip()]
    xpath, suffix = "", ""
    for i, token in enumerate(tokens):
        low = token.strip().lower()
        if low in VALUE_TOKENS:
            suffix = VALUE_TOKENS[low]
            continue
        if i == len(tokens) - 1 and (low in ATTR_TOKENS or low.startswith("data-")):
            suffix = f"/@{token.strip()}"
            continue
        node, pred = token_to_xpath(token)
        if not node:
            continue
        # legado 的 "a@class.gr" 是在 a 自身及后代里筛选，不是取 a 的后代
        if xpath and node.startswith("//*["):
            node = "/descendant-or-self::" + node[2:]
        xpath += node
        if pred:
            xpath = f"({xpath}){pred}"
    return (xpath or f"//{item_tag}") + suffix


def regex_steps_to_js(steps):
    """legado 的 ##正则 是顺序执行的多次替换，逐条生成 replace。"""
    lines = []
    for pattern, repl in steps:
        safe = pattern.replace("/", r"\/")  # JS 正则字面量里的 / 必须转义
        lines.append(f'  result = result.replace(/{safe}/g, "{repl}");')
    body = "\n".join(lines)
    return (
        "@js:\n"
        "if (typeof result === 'string') {\n"
        f"{body}\n"
        "}\n"
        "return result;"
    )


def infer_item_tag(list_xpath):
    """从 list 的 XPath 末段推断列表项标签名。"""
    tags = re.findall(r"//([\w-]+|\*)", list_xpath or "")
    return tags[-1] if tags else "*"


def convert_rule(rule, issues, where, variables=None, item_tag="*"):
    """legado 规则 -> 香色规则字符串，失败时记录到 issues 并返回 ''。"""
    if not rule or not str(rule).strip():
        return ""
    rule = str(rule)
    try:
        if variables:
            rule = expand_get(rule, variables)
        # legado 的 || 是多选一、&& 是结果合并，香色的 || 已被 @js 管道占用，
        # 两者统一降级成 XPath 并集，语义近似(并集 vs 优先)
        branches = []
        for alt in split_top(rule, "||"):
            branches.extend(split_top(alt, "&&"))
        branches = [b for b in branches if b.strip()]

        # 多分支是 legado 的容错写法，逐个尝试，坏分支跳过即可
        ok, failures = [], []
        for branch in branches:
            try:
                converted = rule_to_xpath(branch, item_tag)
            except Unsupported as e:
                failures.append(f"{branch} ({e})")
                continue
            if converted:
                ok.append((converted, branch))
        if not ok:
            if failures:
                issues.append(f"{where}: 需人工改写 -> {'; '.join(failures)}")
            return ""
        if failures:
            issues.append(f"{where}: 部分分支无法转换已丢弃 -> {'; '.join(failures)}")

        xpaths = [x for x, _ in ok]
        if len(xpaths) > 1:
            issues.append(f"{where}: 多分支规则降级处理，需人工确认 -> {rule}")
            # 带 /text() 或 /@attr 后缀时并集写法容易出错，退化成只取首个分支
            if any("/@" in x or "/text()" in x for x in xpaths):
                xpath = xpaths[0]
            else:
                xpath = " | ".join(xpaths)
        else:
            xpath = xpaths[0]

        _, steps = parse_regex_suffix(ok[0][1])
        if steps:
            return f"{xpath}||{regex_steps_to_js(steps)}"
        return xpath
    except Unsupported as e:
        issues.append(f"{where}: {e}，需人工改写 -> {rule}")
        return ""


# ---------------------------------------------------------------- 请求构造


def parse_search_url(search_url):
    """解析 legado searchUrl，返回 (url, method, params_dict)。"""
    search_url = (search_url or "").strip()
    if not search_url:
        return "", "GET", {}

    url, cfg = search_url, {}
    m = re.search(r",\s*(\{.*\})\s*$", search_url, re.S)
    if m:
        url = search_url[: m.start()]
        raw = m.group(1)
        try:
            cfg = json.loads(raw)
        except json.JSONDecodeError:
            try:
                cfg = json.loads(raw.replace("'", '"'))  # legado 允许单引号
            except json.JSONDecodeError:
                cfg = {}

    method = str(cfg.get("method", "GET")).upper()
    params = {}
    for pair in str(cfg.get("body") or "").split("&"):
        if "=" in pair:
            k, v = pair.split("=", 1)
            params[k] = v
    return url, method, params


def js_value(template, encode=False):
    """把含 {{key}}/{{page}} 的模板转成 JS 表达式。

    encode 仅用于直接拼进 URL 字符串的场景；httpParams 里的值香色会自己编码。
    """
    if "{{" not in template:
        return json.dumps(template, ensure_ascii=False)
    key = "${encodeURIComponent(params.keyWord)}" if encode else "${params.keyWord}"
    expr = (
        template.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("{{key}}", key)
        .replace("{{page}}", "${params.pageIndex}")
    )
    return f"`{expr}`"


def build_request_info(host, url, method, params, issues, where):
    if "<js>" in url or "@js:" in url:
        issues.append(f"{where}: searchUrl 内含 JS，需人工改写 -> {url}")
        return ""

    # 书源里的相对地址写法不统一(有的带 /、有的不带)，统一拼成绝对地址
    absolute = urljoin(host + "/", url) if host and not url.startswith("http") else url

    lines = ["@js:", f"let url = {js_value(absolute, encode=True)};", "return {", '  "url": url,']
    if method == "POST":
        lines.append('  "POST": true,')
    if params:
        entries = ", ".join(f'"{k}": {js_value(v)}' for k, v in params.items())
        lines.append(f'  "httpParams": {{{entries}}},')
    lines.append('  "httpHeaders": config.httpHeaders,')
    lines.append('  "cacheTime": 600')
    lines.append("};")
    return "\n".join(lines)


def parse_explore(explore_url):
    """legado exploreUrl -> [(标题, url模板)]，支持 '名称::url' 与 JSON 数组两种写法。"""
    explore_url = (explore_url or "").strip()
    if not explore_url:
        return []
    if explore_url.startswith("["):
        try:
            return [(i.get("title", ""), i.get("url", "")) for i in json.loads(explore_url)]
        except (json.JSONDecodeError, AttributeError):
            return []
    items = []
    for line in explore_url.splitlines():
        if "::" in line:
            title, url = line.split("::", 1)
            items.append((title.strip(), url.strip()))
    return items


# ---------------------------------------------------------------- 书源装配

SOURCE_TYPE_MAP = {0: "text", 1: "audio", 2: "image", 3: "file"}


def build_action(action_id, host, headers, fields):
    action = {
        "actionID": action_id,
        "host": host,
        "parserID": "DOM",
        "responseFormatType": "html",
        "validConfig": "",
    }
    if headers:
        action["httpHeaders"] = headers
    action.update({k: v for k, v in fields.items() if v})
    return action


def convert_source(src, issues):
    name = (src.get("bookSourceName") or "").strip()
    host = (src.get("bookSourceUrl") or "").rstrip("/")
    where = name or host

    headers = {}
    raw_header = src.get("header")
    if raw_header:
        try:
            headers = json.loads(raw_header)
        except (json.JSONDecodeError, TypeError):
            issues.append(f"{where}: header 不是合法 JSON，已忽略 -> {raw_header}")

    rs = src.get("ruleSearch") or {}
    rb = src.get("ruleBookInfo") or {}
    rt = src.get("ruleToc") or {}
    rc = src.get("ruleContent") or {}

    init = rb.get("init") or ""
    variables = parse_put_vars(init)
    if "@put:" in init and not variables:
        issues.append(f"{where}: ruleBookInfo.init 的 @put 解析失败，bookDetail 字段需人工改写 -> {init}")
    elif init and not variables:
        issues.append(f"{where}: ruleBookInfo.init 限定了解析根节点，香色无对应字段已忽略 -> {init}")

    def cv(rule, field, use_vars=False, item_tag="*"):
        return convert_rule(
            rule, issues, f"{where}.{field}", variables if use_vars else None, item_tag
        )

    url, method, params = parse_search_url(src.get("searchUrl", ""))
    search_list = cv(rs.get("bookList"), "ruleSearch.bookList")
    s_tag = infer_item_tag(search_list)
    search_book = build_action(
        "searchBook",
        host,
        headers,
        {
            "requestInfo": build_request_info(host, url, method, params, issues, f"{where}.searchUrl"),
            "list": search_list,
            "bookName": cv(rs.get("name"), "ruleSearch.name", item_tag=s_tag),
            "author": cv(rs.get("author"), "ruleSearch.author", item_tag=s_tag),
            "cover": cv(rs.get("coverUrl"), "ruleSearch.coverUrl", item_tag=s_tag),
            "detailUrl": cv(rs.get("bookUrl"), "ruleSearch.bookUrl", item_tag=s_tag),
            "desc": cv(rs.get("intro"), "ruleSearch.intro", item_tag=s_tag),
            "cat": cv(rs.get("kind"), "ruleSearch.kind", item_tag=s_tag),
            "wordCount": cv(rs.get("wordCount"), "ruleSearch.wordCount", item_tag=s_tag),
            "lastChapterTitle": cv(rs.get("lastChapter"), "ruleSearch.lastChapter", item_tag=s_tag),
        },
    )

    book_detail = build_action(
        "bookDetail",
        host,
        headers,
        {
            "bookName": cv(rb.get("name"), "ruleBookInfo.name", True),
            "author": cv(rb.get("author"), "ruleBookInfo.author", True),
            "cover": cv(rb.get("coverUrl"), "ruleBookInfo.coverUrl", True),
            "desc": cv(rb.get("intro"), "ruleBookInfo.intro", True),
            "cat": cv(rb.get("kind"), "ruleBookInfo.kind", True),
            "wordCount": cv(rb.get("wordCount"), "ruleBookInfo.wordCount", True),
            "lastChapterTitle": cv(rb.get("lastChapter"), "ruleBookInfo.lastChapter", True),
        },
    )

    toc_list = cv(rt.get("chapterList"), "ruleToc.chapterList")
    t_tag = infer_item_tag(toc_list)
    chapter_list = build_action(
        "chapterList",
        host,
        headers,
        {
            "list": toc_list,
            "title": cv(rt.get("chapterName"), "ruleToc.chapterName", item_tag=t_tag),
            "url": cv(rt.get("chapterUrl"), "ruleToc.chapterUrl", item_tag=t_tag),
            "updateTime": cv(rt.get("updateTime"), "ruleToc.updateTime", item_tag=t_tag),
        },
    )
    next_toc = cv(rt.get("nextTocUrl"), "ruleToc.nextTocUrl")
    if next_toc:
        chapter_list["nextPageUrl"] = next_toc
        chapter_list["moreKeys"] = {"maxPage": 200}
    if rb.get("tocUrl"):
        # 香色 chapterList.requestInfo 拿到的 result 是 detailUrl 字符串而非 HTML，
        # 无法执行 legado 那种"从详情页里提取目录地址"的规则
        issues.append(
            f"{where}: ruleBookInfo.tocUrl 需从详情页 HTML 提取，香色无法表达；"
            f"请人工在 chapterList.requestInfo 里用字符串规则推导 -> {rb['tocUrl']}"
        )

    content = cv(rc.get("content"), "ruleContent.content")
    replace_regex = rc.get("replaceRegex")
    if content and replace_regex:
        raw = replace_regex if replace_regex.startswith("##") else "##" + replace_regex
        _, steps = parse_regex_suffix(raw)
        if steps:
            if "||@js:" in content:
                issues.append(f"{where}: content 同时存在选择器正则与 replaceRegex，仅保留前者")
            else:
                content += "||" + regex_steps_to_js(steps)

    chapter_content = build_action("chapterContent", host, headers, {"content": content})
    next_content = cv(rc.get("nextContentUrl"), "ruleContent.nextContentUrl")
    if next_content:
        chapter_content["nextPageUrl"] = next_content
        chapter_content["moreKeys"] = {"maxPage": 50}

    book_world = {}
    explore_items = parse_explore(src.get("exploreUrl"))
    if explore_items:
        re_ = src.get("ruleExplore") or {}
        filters = "_type\n" + "\n".join(f"{t}::{u}" for t, u in explore_items)
        explore_list = cv(re_.get("bookList"), "ruleExplore.bookList")
        e_tag = infer_item_tag(explore_list)
        book_world["分类"] = build_action(
            "bookWorld",
            host,
            headers,
            {
                "requestInfo": (
                    "@js:\n"
                    "let { _type } = params.filters;\n"
                    "let url = _type.replace(/\\{\\{page\\}\\}/g, params.pageIndex);\n"
                    'return { "url": url, "httpHeaders": config.httpHeaders, "cacheTime": 600 };'
                ),
                "list": explore_list,
                "bookName": cv(re_.get("name"), "ruleExplore.name", item_tag=e_tag),
                "author": cv(re_.get("author"), "ruleExplore.author", item_tag=e_tag),
                "cover": cv(re_.get("coverUrl"), "ruleExplore.coverUrl", item_tag=e_tag),
                "detailUrl": cv(re_.get("bookUrl"), "ruleExplore.bookUrl", item_tag=e_tag),
                "moreKeys": {"pageSize": 20, "requestFilters": filters},
                "_sIndex": 0,
            },
        )

    def stub(action_id):
        return {"actionID": action_id, "parserID": "DOM"}

    return name, {
        "enable": 1 if src.get("enabled", True) else 0,
        "sourceName": name,
        "sourceUrl": host,
        "sourceType": SOURCE_TYPE_MAP.get(src.get("bookSourceType", 0), "text"),
        "weight": "9999",
        "miniAppVersion": "2.53.2",
        "lastModifyTime": str(src.get("lastUpdateTime", 0))[:10] + ".0",
        "httpHeaders": headers,
        "searchBook": search_book,
        "bookDetail": book_detail,
        "chapterList": chapter_list,
        "chapterContent": chapter_content,
        "bookWorld": book_world,
        "shudanList": {},
        "shudanDetail": stub("shudanDetail"),
        "searchShudan": stub("searchShudan"),
        "relatedWord": stub("relatedWord"),
        "shupingList": stub("shupingList"),
        "shupingHome": stub("shupingHome"),
    }


# ---------------------------------------------------------------- 校验 & 入口

SKIP_VALIDATE = {
    "actionID", "host", "parserID", "responseFormatType", "validConfig",
    "sourceName", "sourceUrl", "sourceType", "weight", "miniAppVersion",
    "lastModifyTime", "requestInfo",
}


def validate(result, issues):
    """用 lxml 编译每条 XPath，语法错的直接报出来。"""
    if etree is None:
        issues.append("未安装 lxml，跳过 XPath 语法校验")
        return 0
    bad = 0
    for name, src in result.items():
        for action, cfg in src.items():
            if not isinstance(cfg, dict) or action == "httpHeaders":
                continue
            groups = (
                [(f"bookWorld.{k}", v) for k, v in cfg.items()]
                if action == "bookWorld"
                else [(action, cfg)]
            )
            for label, group in groups:
                for field, value in group.items():
                    if field in SKIP_VALIDATE or not isinstance(value, str):
                        continue
                    xpath = value.split("||")[0].strip()
                    if not xpath or xpath.startswith(("@js:", "$")):
                        continue
                    try:
                        etree.XPath(xpath)
                    except etree.XPathSyntaxError as e:
                        bad += 1
                        issues.append(f"{name}.{label}.{field}: XPath 语法错误({e}) -> {xpath}")
    return bad


def main():
    parser = argparse.ArgumentParser(description="阅读(legado)书源 -> 香色书源")
    parser.add_argument("input", nargs="?", default="shuyuan.json")
    parser.add_argument("-o", "--output", default="shuyuan_converted_xs.json")
    parser.add_argument("--report", help="把待人工处理清单写入该文件")
    parser.add_argument("--only", help="只输出指定书源，多个用逗号分隔")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        sources = json.load(f)
    if isinstance(sources, dict):
        sources = [sources]

    if args.only:
        wanted = [n.strip() for n in args.only.split(",")]
        found = {(s.get("bookSourceName") or "").strip() for s in sources}
        missing = [n for n in wanted if n not in found]
        if missing:
            print(f"未找到书源: {missing}", file=sys.stderr)
        order = {n: i for i, n in enumerate(wanted)}
        sources = [s for s in sources if (s.get("bookSourceName") or "").strip() in order]
        sources.sort(key=lambda s: order[(s.get("bookSourceName") or "").strip()])

    issues, result = [], {}
    for src in sources:
        name, converted = convert_source(src, issues)
        if not name:
            issues.append(f"跳过无 bookSourceName 的书源: {src.get('bookSourceUrl')}")
            continue
        result[name] = converted

    bad = validate(result, issues)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"已转换 {len(result)} 个书源 -> {args.output}")
    print(f"XPath 语法错误 {bad} 条，待人工处理 {len(issues)} 项")
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write("\n".join(issues))
        print(f"清单已写入 {args.report}")
    else:
        for item in issues:
            print("  -", item)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
