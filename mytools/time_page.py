
import wx
from datetime import datetime,timezone,timedelta

class TimePage(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.initUI()
    def initUI(self):
        ### 时间戳页面
        self.timestamp_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.timestamp_label = wx.StaticText(self, label="时间戳:")
        self.timestamp_input_text = wx.TextCtrl(self)
        self.timestamp_button = wx.Button(self, label="转换")
        self.timestamp_output_text = wx.TextCtrl(self)

        self.timestamp_sizer.Add(self.timestamp_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.timestamp_sizer.Add(self.timestamp_input_text, 1,wx.EXPAND|wx.ALL, 5)
        self.timestamp_sizer.Add(self.timestamp_button, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.timestamp_sizer.Add(self.timestamp_output_text, 1, wx.EXPAND|wx.ALL, 5)

        self.timing_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.timing_label = wx.StaticText(self, label="时间:")
        self.timing_input_text = wx.TextCtrl(self)
        self.timing_button = wx.Button(self, label="转换")
        self.timing_output_text = wx.TextCtrl(self)

        self.timing_sizer.Add(self.timing_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.timing_sizer.Add(self.timing_input_text, 1, wx.EXPAND|wx.ALL, 5)
        self.timing_sizer.Add(self.timing_button, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.timing_sizer.Add(self.timing_output_text, 1, wx.EXPAND|wx.ALL, 5)
        # 获取当前时间
        current_time = datetime.now()
        # 将当前时间转换为您想要的时间模式，例如：
        formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
        self.timing_input_text.SetValue(formatted_time)

        self.time_sizer = wx.BoxSizer(wx.VERTICAL)
        self.time_sizer.Add(self.timestamp_sizer, 0, wx.EXPAND|wx.ALL, 5)
        self.time_sizer.Add(self.timing_sizer, 0, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(self.time_sizer)

        self.timestamp_button.Bind(wx.EVT_BUTTON, self.OnTimestamp)
        self.timing_button.Bind(wx.EVT_BUTTON, self.OnTiming)

    def OnTimestamp(self, event):
        timestamp_input = self.timestamp_input_text.GetValue()
        datatime_output = timestamp_to_datetime(timestamp_input)
        self.timestamp_output_text.SetValue(datatime_output)

    def OnTiming(self,event):
        timing_input = self.timing_input_text.GetValue()
        timing_output = datetime_to_timestamp(timing_input)
        self.timing_output_text.SetValue(str(timing_output))
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