#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取中国气象局最近7天天气数据并发送到Zulip
"""

import requests
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


# Zulip配置
ZULIP_WEBHOOK_URL = "************"

# 中国气象局API配置
# 7天天气预报网页
WEATHER_7D_URL = "http://www.weather.com.cn/weather/"
# 15天天气预报网页
WEATHER_15D_URL = "http://www.weather.com.cn/weather15d/"

# 城市代码（例如：101010100 是北京）
# 可以在 http://www.weather.com.cn/ 查询城市代码
CITY_CODE = "101010100"  # 北京
CITY_NAME = "北京"

def get_weather_data(city_code):
    """
    从中国天气网获取指定城市的7天天气数据
    解析HTML页面获取天气信息
    """
    try:
        url = f"{WEATHER_7D_URL}{city_code}.shtml"
        print(f"正在请求: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找7天天气预报列表
        weather_list = []
        
        # 天气数据在 id="7d" 的 ul 列表中
        weather_div = soup.find('ul', class_='t clearfix')
        if not weather_div:
            weather_div = soup.find('div', id='7d')
            if weather_div:
                weather_div = weather_div.find('ul', class_='t clearfix')
        
        if weather_div:
            items = weather_div.find_all('li')
            for item in items:
                try:
                    # 日期
                    date_elem = item.find('h1')
                    date_str = date_elem.text if date_elem else ''
                    
                    # 天气状况
                    weather_elem = item.find('p', class_='wea')
                    weather_str = weather_elem.text if weather_elem else ''
                    
                    # 温度
                    temp_elem = item.find('p', class_='tem')
                    if temp_elem:
                        temp_high = temp_elem.find('span')
                        temp_low = temp_elem.find('i')
                        high = temp_high.text.replace('℃', '') if temp_high else ''
                        low = temp_low.text.replace('℃', '') if temp_low else ''
                    else:
                        high = low = ''
                    
                    # 风向风力
                    wind_elem = item.find('p', class_='win')
                    if wind_elem:
                        wind_dir_elem = wind_elem.find('em')
                        wind_dir = ''
                        if wind_dir_elem:
                            spans = wind_dir_elem.find_all('span')
                            if spans:
                                wind_dir = spans[0].get('title', '')
                        wind_level = wind_elem.find('i')
                        wind_level_str = wind_level.text if wind_level else ''
                        wind_str = f"{wind_dir} {wind_level_str}"
                    else:
                        wind_str = ''
                    
                    weather_list.append({
                        'date': date_str,
                        'weather': weather_str,
                        'high': high,
                        'low': low,
                        'wind': wind_str.strip()
                    })
                except Exception as e:
                    print(f"解析天气项目失败: {e}")
                    continue
        
        if weather_list:
            print(f"✅ 成功获取 {len(weather_list)} 天的天气数据")
            return weather_list
        else:
            print("⚠️ 未找到预报数据")
            return None
            
    except requests.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
        return None
    except Exception as e:
        print(f"❌ 获取天气数据失败: {e}")
        return None


def format_weather_message(weather_list, city_name):
    """
    格式化天气信息为易读的文本
    weather_list: 从HTML解析的天气数据列表
    """
    if not weather_list:
        return "未能获取天气数据"
    
    message = "=" * 60 + "\n\n"
    
    for day in weather_list:
        # 从HTML解析的数据格式
        date = day.get('date', '')
        weather_str = day.get('weather', '')
        high = day.get('high', '')
        low = day.get('low', '')
        wind = day.get('wind', '')
        
        message += f"📆 {date}\n"
        message += f"   🌤️  天气: {weather_str}\n"
        if high and low:
            message += f"   🌡️  温度: {low}°C ~ {high}°C\n"
        elif low:
            message += f"   🌡️  温度: {low}°C\n"
        if wind:
            message += f"   💨 风力: {wind}\n"
        message += "-" * 60 + "\n"
    
    return message


def send_to_zulip(message):
    """
    发送消息到Zulip
    使用Zabbix webhook格式
    """
    trigger = f"📍{CITY_NAME}- 未来7天天气预报\n"
    trigger += f"📅 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    payload = {
        "hostname": "天气预报服务",
        "severity": "Information",
        "status": "OK",
        "item": message,
        "trigger": trigger,
        "link": "http://www.weather.com.cn/"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            ZULIP_WEBHOOK_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ 天气信息已成功发送到Zulip")
            return True
        else:
            print(f"❌ 发送失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 发送到Zulip时出错: {e}")
        return False


def main():
    """
    主函数：获取天气数据并发送到Zulip
    """
    print("=" * 60)
    print("天气预报获取与推送服务")
    print("=" * 60)
    print(f"城市: {CITY_NAME} (代码: {CITY_CODE})")
    print("正在获取天气数据...\n")
    
    # 使用 get_weather_data 获取真实的7天天气预报
    weather_data = get_weather_data(CITY_CODE)
    
    if not weather_data:
        print("❌ 未能获取天气数据")
        error_msg = f"{CITY_NAME}天气数据获取失败\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        send_to_zulip(error_msg)
        return
    
    print(f"✅ 成功获取 {len(weather_data)} 天的天气数据\n")
    
    # 格式化消息
    message = format_weather_message(weather_data, CITY_NAME)
    
    print("=" * 60)
    print("准备发送的消息预览:")
    print("=" * 60)
    print(message)
    
    # 发送到Zulip
    print("\n正在发送到Zulip...")
    success = send_to_zulip(message)
    
    if success:
        print("\n✅ 任务完成")
    else:
        print("\n❌ 任务失败")


if __name__ == "__main__":
    main()
