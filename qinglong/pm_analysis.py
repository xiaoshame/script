import requests
import json
from datetime import datetime, timedelta
import time

def get_local_timestamps():
    """获取当前时间和一小时前的时间戳（毫秒）"""
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)
    
    # 转换为毫秒时间戳
    to_ts = int(time.mktime(now.timetuple()) * 1000)
    from_ts = int(time.mktime(one_hour_ago.timetuple()) * 1000)
    
    return from_ts, to_ts

def get_device_data(request_id, panel_id, panel_title, field_name):
    """获取设备数据的通用函数"""
    url = "https://gra.91cost.cn/api/ds/query"
    
    # 获取本地时间戳
    from_ts, to_ts = get_local_timestamps()
    
    # 查询参数
    params = {
        "ds_type": "influxdb",
        "requestId": request_id
    }

    # 请求头
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7,zh-TW;q=0.6",
        "content-type": "application/json",
        "origin": "https://gra.91cost.cn",
        "priority": "u=1, i",
        "referer": "https://gra.91cost.cn/d/air001/air-single?orgId=1&from=now-1h&to=now&var-MAC=EC62608688BC&timezone=browser&var-interval=30s&var-NAME=NewDevice-EC62608688BC",
        "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "x-dashboard-title": "air-single",
        "x-dashboard-uid": "air001",
        "x-datasource-uid": "fdotvxo814zy8a",
        "x-grafana-device-id": "15fdd78d678c9f1bd64255f1305d0258",
        "x-grafana-org-id": "1",
        "x-panel-id": panel_id,
        "x-panel-plugin-id": "timeseries",
        "x-panel-title": panel_title,
        "x-plugin-id": "influxdb"
    }
    
    # 请求体数据
    data = {
        "queries": [{
            "alias": "Percent Chance",
            "datasource": {
                "type": "influxdb",
                "uid": "fdotvxo814zy8a"
            },
            "groupBy": [
                {"params": ["$__interval"], "type": "time"},
                {"params": ["previous"], "type": "fill"}
            ],
            "measurement": "weatherflow_forecast_hourly",
            "orderByTime": "ASC",
            "policy": "default",
            "query": f"""from(bucket: "DAIKIN")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "device_data")
  |> filter(fn: (r) => r["_field"] == "{field_name}")
  |> filter(fn: (r) => r["name"] == "EC62608688BC")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> map(fn: (r) => ({{ r with display_name: r._field }}))
  |> yield(name: "mean")""",
            "refId": "A",
            "resultFormat": "time_series",
            "select": [[
                {"params": ["precip_probability"], "type": "field"},
                {"params": [], "type": "first"}
            ]],
            "tags": [
                {
                    "key": "station_name",
                    "operator": "=~",
                    "value": "/^$station_name$/"
                },
                {
                    "condition": "AND",
                    "key": "forecast_hourly_days_out",
                    "operator": "=",
                    "value": "0"
                }
            ],
            "tz": "$tz",
            "datasourceId": 1,
            "intervalMs": 30000,
            "maxDataPoints": 860
        }],
        "from": str(from_ts),
        "to": str(to_ts)
    }
    
    try:
        response = requests.post(url, params=params, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求出错: {e}")
        return None

def get_pm25_data():
    """获取PM2.5数据"""
    return get_device_data("SQR109", "90", "%E5%8D%95%E5%83%8F%E7%BA%BF", "PM25")

def parse_pm25_data(data):
    """解析PM2.5数据，返回时间戳和对应的PM2.5值"""
    if not data or 'results' not in data:
        return []
    
    try:
        frames = data['results']['A']['frames']
        if not frames:
            return []
            
        values = frames[0]['data']['values']
        timestamps = values[0]  # 时间戳列表
        pm25_values = values[1]  # PM2.5值列表
        
        # 将时间戳转换为人类可读的格式并与PM2.5值配对
        parsed_data = []
        for ts, pm25 in zip(timestamps, pm25_values):
            # 将毫秒时间戳转换为datetime对象
            dt = datetime.fromtimestamp(ts / 1000)
            parsed_data.append({
                'timestamp': dt.strftime('%Y-%m-%d %H:%M:%S'),
                'pm25': pm25
            })
        
        return parsed_data
            
    except (KeyError, IndexError) as e:
        print(f"解析数据时出错: {e}")
        return []

def analyze_device_data(parsed_data, value_key='value'):
    """分析设备数据，计算统计信息"""
    if not parsed_data:
        return None
        
    values = [item[value_key] for item in parsed_data]
    
    return {
        'count': len(values),
        'average': sum(values) / len(values),
        'max': max(values),
        'min': min(values),
        'latest': parsed_data[-1][value_key]
    }

def analyze_pm25_data(parsed_data):
    """分析PM2.5数据，计算统计信息"""
    return analyze_device_data(parsed_data, 'pm25')

def get_temperature_data():
    """获取温度数据"""
    return get_device_data("SQR100", "89", "%E6%B8%A9%E5%BA%A6", "CurrentTemperature")

def parse_temperature_data(data):
    """解析温度数据，返回时间戳和对应的温度值"""
    if not data or 'results' not in data:
        return []
    
    try:
        frames = data['results']['A']['frames']
        if not frames:
            return []
            
        values = frames[0]['data']['values']
        timestamps = values[0]  # 时间戳列表
        temp_values = values[1]  # 温度值列表
        
        # 将时间戳转换为人类可读的格式并与温度值配对
        parsed_data = []
        for ts, temp in zip(timestamps, temp_values):
            # 将毫秒时间戳转换为datetime对象
            dt = datetime.fromtimestamp(ts / 1000)
            parsed_data.append({
                'timestamp': dt.strftime('%Y-%m-%d %H:%M:%S'),
                'value': temp
            })
        
        return parsed_data
            
    except (KeyError, IndexError) as e:
        print(f"解析温度数据时出错: {e}")
        return []

def analyze_temperature_data(parsed_data):
    """分析温度数据，计算统计信息"""
    return analyze_device_data(parsed_data)

if __name__ == "__main__":
    # 获取并分析PM2.5数据
    print("正在获取PM2.5数据...")
    pm25_result = get_pm25_data()
    if pm25_result:
        pm25_data = parse_pm25_data(pm25_result)
        pm25_stats = analyze_pm25_data(pm25_data)
        if pm25_stats:
            info = f"平均值: {pm25_stats['average']:.1f}\n"
            info += f"最大值: {pm25_stats['max']}\n"
            info += f"最小值: {pm25_stats['min']}\n"
            info += f"当前值: {pm25_stats['latest']}\n"
            QLAPI.systemNotify({"title": "PM2.5 数据统计", "content": info})

    # 获取并分析温度数据
    print("\n正在获取温度数据...")
    temp_result = get_temperature_data()
    if temp_result:
        temp_data = parse_temperature_data(temp_result)
        temp_stats = analyze_temperature_data(temp_data)
        if temp_stats:
            info = f"平均值: {temp_stats['average']:.1f}\n"
            info += f"最大值: {temp_stats['max']}\n"
            info += f"最小值: {temp_stats['min']}\n"
            info += f"当前值: {temp_stats['latest']}\n"
            QLAPI.systemNotify({"title": "温度 数据统计", "content": info})
