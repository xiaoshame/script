"""
QDII基金实时溢价率与估值数据解析脚本
获取溢价率大于3%的基金信息
"""
import requests
import re
from bs4 import BeautifulSoup
from typing import List, Dict
import json
from datetime import datetime

# Zulip webhook 配置
# 注意：该 Webhook 采用 Zabbix 格式，需要 topic, to, content 字段
ZULIP_WEBHOOK_URL = "***********"
# 默认发送目标频道（请根据您的 Zulip 频道名称修改）
TARGET_ZULIP_STREAM = "基金套利通知" 


def fetch_html(url: str = "https://www.haoetf.com/") -> str:
    """
    请求网页获取HTML内容
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print(f"正在请求: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        print(f"状态码: {response.status_code}")
        # 如果请求失败，抛出异常，否则返回内容
        response.raise_for_status() 
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        # 在失败时返回 None 而不是抛出异常，让主函数处理
        return None


def fetch_multiple_urls(urls: List[str]) -> Dict[str, str]:
    """
    请求多个网页获取HTML内容
    """
    results = {}
    for url in urls:
        html_content = fetch_html(url)
        results[url] = html_content
    return results


def parse_html(html: str, include_latest_premium: bool = True) -> List[Dict[str, str]]:
    """
    解析HTML，提取基金数据
    """
    if html is None:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    funds = []
    
    # 找到两个表格 - LOF和ETF
    tables = soup.find_all('table', class_='table table-striped table-sm text-right table-hover')
    
    print(f"找到 {len(tables)} 个表格")
    
    for table_idx, table in enumerate(tables):
        table_type = "LOF基金" if table_idx == 0 else "ETF基金"
        print(f"\n解析第 {table_idx + 1} 个表格 ({table_type}):")
        
        rows = table.find_all('tr')
        print(f"  表格行数: {len(rows)}")
        
        for row in rows[1:]:  # 跳过表头
            cells = row.find_all('td')
            # 确保行有足够的单元格来提取所有数据
            if len(cells) < 18: 
                continue
            
            try:
                # 提取基金信息
                code = cells[0].get_text(strip=True)
                name = cells[1].get_text(strip=True)
                
                # 实时溢价率 (第4列，索引3)
                real_time_premium_text = cells[3].get_text(strip=True)
                
                # 申购限额 (倒数第4列，索引 -4)
                purchase_limit = cells[-4].get_text(strip=True)
                
                # 解析溢价率数值
                real_time_premium = parse_percentage(real_time_premium_text)
                
                fund_info = {
                    'code': code,
                    'name': name,
                    'table_type': table_type,
                    'real_time_premium': real_time_premium,
                    'purchase_limit': purchase_limit,
                    'raw_real_time_premium': real_time_premium_text,
                }
                
                # 如果需要，解析最新溢价率 (第6列，索引5)
                if include_latest_premium:
                    latest_premium_text = cells[5].get_text(strip=True)
                    latest_premium = parse_percentage(latest_premium_text)
                    fund_info['latest_premium'] = latest_premium
                    fund_info['raw_latest_premium'] = latest_premium_text
                
                funds.append(fund_info)
                
            except Exception as e:
                print(f"  解析行失败: {e}")
                continue
    
    return funds


def parse_percentage(text: str) -> float:
    """
    从文本中提取百分比数值
    """
    if text == '-' or text == '':
        return None
    
    # 匹配可能的负号、数字和小数点
    match = re.search(r'-?\d+\.?\d*', text)
    if match:
        return float(match.group())
    
    return None


def filter_high_premium_funds(funds: List[Dict], threshold: float = 3.0) -> List[Dict]:
    """
    筛选实时溢价率大于阈值的基金
    """
    result = []
    for fund in funds:
        real_time_premium = fund['real_time_premium']
        
        if real_time_premium is not None and real_time_premium > threshold:
            result.append(fund)
    
    return result


def output_results(high_premium_funds: List[Dict], threshold: float = 3.0) -> None:
    """
    输出结果并发送到Zulip（使用Zabbix webhook格式）
    """
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    has_latest_premium = any('latest_premium' in fund for fund in high_premium_funds)

    # --- 构建 Zabbix Webhook 格式的消息 ---
    if not high_premium_funds:
        # 正常情况
        severity = "Info"
        status = "OK"
        item = "QDII基金溢价率正常"
        trigger = "所有基金实时溢价率均低于阈值"
    else:
        # 警报情况
        severity = "High"
        status = "PROBLEM"
        item = "代码 基金名 实时溢价 最新溢价 限购额度"
        trigger = f"高溢价基金数量：{len(high_premium_funds)} 支"
        
        # 构建基金列表信息
        funds_info = []
        for fund in high_premium_funds:
            info = f"{fund['code']} {fund['name']} {fund['raw_real_time_premium']}"
            if has_latest_premium:
                info += f" {fund.get('raw_latest_premium', '-')}"
            info += f" {fund['purchase_limit']}"
            funds_info.append(info)
        item += "\n" + "\n".join(funds_info)

    # 构建 Zulip payload (使用Zabbix格式)
    zulip_payload = {
        "hostname": "QDII监控",
        "severity": severity,
        "status": status,
        "item": item,
        "trigger": trigger,
        "link": "https://www.haoetf.com/"
    }

    print(f"--- 正在向 URL 发送消息 ---")
    print(f"URL: {ZULIP_WEBHOOK_URL}")
    print(f"Payload: {json.dumps(zulip_payload, ensure_ascii=False, indent=2)}")

    try:
        response = requests.post(
            ZULIP_WEBHOOK_URL,
            headers={"Content-Type": "application/json; charset=utf-8"},
            data=json.dumps(zulip_payload, ensure_ascii=False).encode('utf-8')
        )

        print("\n--- 响应结果 ---")
        print(f"状态码 (Status Code): {response.status_code}")

        if response.status_code == 200:
            print("✅ Zulip 消息发送成功。")
            print("响应体内容:", response.text)
        else:
            print(f"❌ 发送失败：返回非 200 状态码。")
            print(f"响应内容 (Response Body): {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ 连接错误：无法连接到目标 URL 或发生其他请求异常。")
        print(f"错误信息: {e}")


def main():
    """主函数"""
    urls = [
        "https://www.haoetf.com/",
        "https://www.haoetf.com/lof"
    ]
    
    html_dict = fetch_multiple_urls(urls)
    all_funds = []
    
    for url, html in html_dict.items():
        if html is None:
            print(f"\n跳过 {url} (请求失败)")
            continue
        
        print(f"\n处理: {url}")
        # 只有主页才有最新溢价率数据
        include_latest = not url.endswith('/lof')
        funds = parse_html(html, include_latest_premium=include_latest)
        all_funds.extend(funds)
        print(f"从此URL解析出 {len(funds)} 支基金")
    
    if not all_funds:
        print("无法解析任何基金数据，程序结束。")
        output_results([]) # 发送空警报通知
        return

    print(f"\n共解析出 {len(all_funds)} 支基金")
    
    # 筛选溢价率 > 3% 的基金
    print("\n筛选溢价率 > 3% 的基金...")
    threshold_value = 3.0
    high_premium_funds = filter_high_premium_funds(all_funds, threshold=threshold_value)
    
    # 按实时溢价率降序排序
    high_premium_funds.sort(key=lambda x: x['real_time_premium'], reverse=True)
    
    # 输出结果
    output_results(high_premium_funds, threshold=threshold_value)


if __name__ == '__main__':
    # 确保requests库和beautifulsoup4库已安装: pip install requests beautifulsoup4
    main()