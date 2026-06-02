#!/usr/bin/env python3
"""V2Ray 订阅转换脚本 - 将订阅链接转换为 V2Ray 配置文件"""

import sys
import json
import base64
import re
from urllib.parse import urlparse, parse_qs, unquote
from urllib.request import urlopen, Request
from urllib.error import URLError


def download_subscription(url: str) -> str:
    """下载订阅内容"""
    req = Request(url, headers={"User-Agent": "V2RaySubConverter/1.0"})
    try:
        with urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except URLError as e:
        print(f"错误: 订阅下载失败 - {e}")
        sys.exit(1)


def decode_base64(data: str) -> str:
    """base64 解码，自动补齐 padding"""
    data = data.strip()
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    try:
        return base64.b64decode(data).decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"错误: base64 解码失败 - {e}")
        sys.exit(1)


def parse_vmess(link: str) -> dict:
    """解析 vmess:// 链接"""
    raw = link.replace("vmess://", "", 1).strip()
    data = json.loads(decode_base64(raw))

    return {
        "address": data.get("add", ""),
        "port": int(data.get("port", 443)),
        "user_id": data.get("id", ""),
        "alter_id": int(data.get("aid", 0)),
        "network": data.get("net", "tcp"),
        "path": data.get("path", ""),
        "tls": data.get("tls", "none"),
        "host": data.get("host", ""),
    }


def parse_trojan(link: str) -> dict:
    """解析 trojan:// 链接"""
    # trojan://password@server:port?params#remarks
    link = link.strip()
    without_scheme = link.replace("trojan://", "", 1)

    # 去掉 #remarks
    if "#" in without_scheme:
        without_scheme = without_scheme.split("#")[0]

    password, rest = without_scheme.split("@", 1)
    password = unquote(password)

    # 分离参数
    params_str = ""
    if "?" in rest:
        server_part, params_str = rest.split("?", 1)
    else:
        server_part = rest

    address, port_str = server_part.rsplit(":", 1)
    port = int(port_str)

    params = parse_qs(params_str)
    allow_insecure = "allowInsecure" in params and params["allowInsecure"][0] == "1"

    return {
        "address": address,
        "port": port,
        "password": password,
        "allow_insecure": allow_insecure,
    }


def parse_ss(link: str) -> dict:
    """解析 ss:// 链接"""
    # ss://base64(method:password)@server:port#remarks
    # 或 ss://base64(method:password@server:port)#remarks
    link = link.strip()
    without_scheme = link.replace("ss://", "", 1)

    # 去掉 #remarks
    if "#" in without_scheme:
        without_scheme = without_scheme.split("#")[0]

    if "@" in without_scheme:
        # 格式: base64(method:password)@server:port
        encoded_part, server_part = without_scheme.split("@", 1)
        decoded = decode_base64(encoded_part)
        method, password = decoded.split(":", 1)
        address, port_str = server_part.rsplit(":", 1)
    else:
        # 整体 base64 编码
        decoded = decode_base64(without_scheme)
        match = re.match(r"^(.+?):(.+?)@(.+?):(\d+)$", decoded)
        if not match:
            print("错误: 无法解析 ss 链接")
            sys.exit(1)
        method, password, address, port_str = match.groups()

    return {
        "method": method,
        "password": password,
        "address": address,
        "port": int(port_str),
    }


def build_inbounds() -> list:
    """构建通用入站配置"""
    return [
        {
            "port": 10808,
            "protocol": "socks",
            "sniffing": {"enabled": True, "destOverride": ["http", "tls"]},
            "settings": {"auth": "noauth"},
        },
        {
            "port": 10809,
            "protocol": "http",
            "sniffing": {"enabled": True, "destOverride": ["http", "tls"]},
        },
    ]


def build_routing() -> dict:
    """构建通用路由配置"""
    return {
        "domainStrategy": "IPOnDemand",
        "rules": [
            {
                "type": "field",
                "ip": ["geoip:private"],
                "outboundTag": "direct",
            }
        ],
    }


def build_vmess_config(node: dict) -> dict:
    """生成 vmess 协议的 V2Ray 配置"""
    stream_settings: dict = {"network": node["network"]}

    # TLS 设置
    if node["tls"] and node["tls"] != "none":
        stream_settings["security"] = node["tls"]
        stream_settings["tlsSettings"] = {"serverName": node["host"]}
    else:
        stream_settings["security"] = "none"

    # 传输层设置
    if node["network"] == "ws":
        stream_settings["wsSettings"] = {
            "path": node["path"],
            "headers": {"Host": node["host"]},
        }
    elif node["network"] == "tcp":
        stream_settings["tcpSettings"] = {}

    outbound = {
        "protocol": "vmess",
        "settings": {
            "vnext": [
                {
                    "address": node["address"],
                    "port": node["port"],
                    "users": [
                        {
                            "id": node["user_id"],
                            "alterId": node["alter_id"],
                            "security": "auto",
                        }
                    ],
                }
            ]
        },
        "streamSettings": stream_settings,
    }

    return {
        "log": {"loglevel": "warning"},
        "inbounds": build_inbounds(),
        "outbounds": [outbound, {"protocol": "freedom", "tag": "direct"}],
        "routing": build_routing(),
    }


def build_trojan_config(node: dict) -> dict:
    """生成 trojan 协议的 V2Ray 配置"""
    outbound = {
        "protocol": "trojan",
        "settings": {
            "servers": [
                {
                    "address": node["address"],
                    "port": node["port"],
                    "password": node["password"],
                }
            ]
        },
        "streamSettings": {
            "network": "tcp",
            "security": "tls",
            "tlsSettings": {
                "serverName": node["address"],
                "allowInsecure": node["allow_insecure"],
            },
        },
    }

    return {
        "log": {"loglevel": "warning"},
        "inbounds": build_inbounds(),
        "outbounds": [outbound, {"protocol": "freedom", "tag": "direct"}],
        "routing": build_routing(),
    }


def build_ss_config(node: dict) -> dict:
    """生成 shadowsocks 协议的 V2Ray 配置"""
    outbound = {
        "protocol": "shadowsocks",
        "settings": {
            "servers": [
                {
                    "address": node["address"],
                    "port": node["port"],
                    "method": node["method"],
                    "password": node["password"],
                }
            ]
        },
    }

    return {
        "log": {"loglevel": "warning"},
        "inbounds": build_inbounds(),
        "outbounds": [outbound, {"protocol": "freedom", "tag": "direct"}],
        "routing": build_routing(),
    }


def main():
    if len(sys.argv) != 3:
        print(f"用法: {sys.argv[0]} 订阅链接 输出配置文件")
        print(f"例如: {sys.argv[0]} https://example.com/sub 配置文件.json")
        sys.exit(1)

    sub_url = sys.argv[1]
    output_file = sys.argv[2]

    print("=== V2Ray 订阅转换脚本 (Python) ===")
    print(f"订阅链接: {sub_url[:30]}...")
    print(f"输出文件: {output_file}")
    print()

    # 1. 下载订阅内容
    print("[1/5] 下载订阅内容...")
    raw_content = download_subscription(sub_url)

    if "<html>" in raw_content.lower():
        print("错误: 订阅下载失败，服务器返回 HTML 内容:")
        print("\n".join(raw_content.splitlines()[:5]))
        sys.exit(1)

    # 2. 解码
    print("[2/5] 解码订阅内容...")
    decoded = decode_base64(raw_content)

    # 3. 检查节点类型
    print("[3/5] 检查节点类型...")
    lines = [line.strip() for line in decoded.splitlines() if line.strip()]
    print(f"找到 {len(lines)} 个节点")

    # 按优先级选择协议: vmess > trojan > ss
    protocol = None
    selected_link = None

    for line in lines:
        if line.startswith("vmess://"):
            protocol = "vmess"
            selected_link = line
            print("找到 vmess 节点，优先使用")
            break

    if not protocol:
        for line in lines:
            if line.startswith("trojan://"):
                protocol = "trojan"
                selected_link = line
                print("找到 trojan 节点，将使用 trojan 协议")
                break

    if not protocol:
        for line in lines:
            if line.startswith("ss://"):
                protocol = "ss"
                selected_link = line
                print("找到 ss 节点，将使用 shadowsocks 协议")
                break

    if not protocol:
        print("错误: 未找到支持的节点类型 (vmess/trojan/ss)")
        sys.exit(1)

    # 4. 解析节点
    print("[4/5] 解析节点信息...")

    if protocol == "vmess":
        node = parse_vmess(selected_link)
        print("节点信息:")
        print(f"  协议: vmess")
        print(f"  地址: {node['address']}")
        print(f"  端口: {node['port']}")
        print(f"  用户ID: {node['user_id'][:8]}...")
        print(f"  alterID: {node['alter_id']}")
        print(f"  传输协议: {node['network']}")
        print(f"  TLS: {node['tls']}")
        config = build_vmess_config(node)

    elif protocol == "trojan":
        node = parse_trojan(selected_link)
        print("节点信息:")
        print(f"  协议: trojan")
        print(f"  地址: {node['address']}")
        print(f"  端口: {node['port']}")
        config = build_trojan_config(node)

    elif protocol == "ss":
        node = parse_ss(selected_link)
        print("节点信息:")
        print(f"  协议: shadowsocks")
        print(f"  地址: {node['address']}")
        print(f"  端口: {node['port']}")
        print(f"  加密方式: {node['method']}")
        config = build_ss_config(node)

    # 5. 写入配置文件
    print("[5/5] 生成 V2Ray 配置文件...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"\n配置已保存到 {output_file}")
    print(f"使用以下命令启动 V2Ray:")
    print(f"v2ray -c {output_file}")
    print()
    print("使用以下命令设置代理环境变量:")
    print("export http_proxy=http://127.0.0.1:10809")
    print("export https_proxy=http://127.0.0.1:10809")
    print()
    print("或使用 SOCKS5 代理:")
    print("export http_proxy=socks5://127.0.0.1:10808")
    print("export https_proxy=socks5://127.0.0.1:10808")


if __name__ == "__main__":
    main()
