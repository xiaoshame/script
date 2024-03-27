
from datetime import datetime,timezone,timedelta

def timestamp_to_datetime(timestamp):
    if len(timestamp) == 10:
        beijing_timezone = timezone(timedelta(hours=8))
        # 将时间戳转换为日期时间对象（以UTC+8时区显示）
        date_time_obj = datetime.fromtimestamp(int(timestamp), beijing_timezone)
        return date_time_obj.strftime('%Y-%m-%d %H:%M:%S')
    elif len(timestamp) == 13:
        # 将毫秒时间戳转换为秒
        seconds = int(timestamp) / 1000.0
        # 提取毫秒部分（取整数部分将使末尾的零被忽略）
        milliseconds = int(int(timestamp) % 1000)
        # 创建UTC+8时区
        beijing_timezone = timezone(timedelta(hours=8))
        # 将时间戳转换为日期时间对象（以UTC+8时区显示）
        date_time_obj = datetime.fromtimestamp(seconds, beijing_timezone)
        # 格式化时间
        return date_time_obj.strftime('%Y-%m-%d %H:%M:%S') + f'.{milliseconds}'
    else:
        return "时间戳长度不对"

# 日期时间转换为时间戳（支持秒和毫秒）
def datetime_to_timestamp(dt):

    # 日期时间字符串
    try:
        if '.' in dt:
            date_time_obj = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S.%f')
        else:
            date_time_obj = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
    except Exception as e:
        return e

    # 假设你的日期时间是UTC，如果不是你需要相对于UTC调整它
    # 如果是其他时区，你需要根据相应的时区进行转换
    # 创建北京时间时区（UTC+8）
    beijing_timezone = timezone(timedelta(hours=8))
    date_time_obj = date_time_obj.replace(tzinfo=beijing_timezone)

    # 转换为时间戳（从epoch开始计算的秒数）
    if '.' in dt:
        return int(round(date_time_obj.timestamp() * 1000))
    else:
        return int(date_time_obj.timestamp())