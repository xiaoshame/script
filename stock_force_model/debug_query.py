# -*- coding: utf-8 -*-
import sqlite3
import hashlib
import requests

conn = sqlite3.connect('rss_news.db')
cur = conn.cursor()

print("=== 数据库中金十数据的最新10条标题 ===")
cur.execute("SELECT id, guid, title, pub_date FROM news WHERE source_name LIKE '%金十%' ORDER BY id DESC LIMIT 10")
db_titles = set()
for row in cur.fetchall():
    db_titles.add(row[2].strip())
    print(f"[{row[3]}] {row[2][:60]}")

print(f"\n=== 统计金十数据总量: {len(db_titles)} 条 ===")

print("\n=== 当前 RSS 源中的新闻 ===")
import xml.etree.ElementTree as ET
try:
    response = requests.get("https://rsshub.rss.zgdnz.cc/jin10", headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    root = ET.fromstring(response.content)
    
    rss_titles = []
    for item in root.findall('.//item'):
        title = item.find('title')
        if title is not None and title.text:
            rss_titles.append(title.text.strip())
    
    print(f"RSS 源共有 {len(rss_titles)} 条新闻")
    
    # 比较新闻
    new_count = 0
    existing_count = 0
    
    print("\n=== 对比分析 ===")
    for title in rss_titles[:15]:
        guid = hashlib.md5(title.strip().encode('utf-8')).hexdigest()
        cur.execute("SELECT id FROM news WHERE guid = ?", (guid,))
        if cur.fetchone():
            print(f"[已存在] {title[:50]}...")
            existing_count += 1
        else:
            print(f"[新记录] {title[:50]}...")
            new_count += 1
    
    print(f"\n总结: RSS源中有 {new_count} 条新记录, {existing_count} 条已存在")
    
except Exception as e:
    print(f"获取 RSS 失败: {e}")

conn.close()
