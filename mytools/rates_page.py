
import wx
import threading
from rates import Rates

class RatesPage(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.rates = Rates()
        self.initUI()

    def initUI(self):
        # 初始化方法
        ### 汇率页面
        self.rates_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # 创建ComboBox
        self.rates_input_combo = wx.ComboBox(self, choices=self.rates.currency_choices, style=wx.CB_READONLY)
        self.rates_input_label = wx.TextCtrl(self,value="1")
        self.rates_label = wx.StaticText(self, label="->")
        self.rates_output_combo = wx.ComboBox(self, choices=self.rates.currency_choices, style=wx.CB_READONLY)
        self.rates_output_label = wx.TextCtrl(self, style=wx.TE_READONLY)

        self.rates_input_combo.SetMinSize(wx.Size(200, 50))
        self.rates_input_combo.SetMaxSize(wx.Size(200, 50))

        self.rates_output_combo.SetMinSize(wx.Size(200, 50))
        self.rates_output_combo.SetMaxSize(wx.Size(200, 50))

        self.rates_input_label.SetMinSize(wx.Size(100, 25))
        self.rates_input_label.SetMaxSize(wx.Size(100, 25))

        self.rates_output_label.SetMinSize(wx.Size(100, 25))
        self.rates_output_label.SetMaxSize(wx.Size(100, 25))

        self.rates_sizer.Add(self.rates_input_combo, 0, wx.EXPAND|wx.ALL,5)
        self.rates_sizer.Add(self.rates_input_label, 0, wx.EXPAND|wx.ALL,5)
        self.rates_sizer.Add(self.rates_label, 0, wx.EXPAND|wx.ALL,5)
        self.rates_sizer.Add(self.rates_output_combo, 0, wx.EXPAND|wx.ALL,5)
        self.rates_sizer.Add(self.rates_output_label, 0, wx.EXPAND|wx.ALL,5)
        
        # 绑定事件处理函数
        self.rates_input_label.Bind(wx.EVT_CHAR, self.on_in_label_char)
        self.rates_input_label.Bind(wx.EVT_TEXT, self.on_in_label_text)
        self.rates_input_combo.Bind(wx.EVT_TEXT, self.on_in_combo_select)
        self.rates_output_combo.Bind(wx.EVT_TEXT, self.on_out_combo_select)

        self.SetSizer(self.rates_sizer)

    def on_in_label_char(self, event):
        # 获取按键值
        key_code = event.GetKeyCode()

        # 如果按键是数字或者是删除键（ASCII码8），则允许输入
        if chr(key_code).isdigit() or key_code == wx.WXK_BACK:
            event.Skip()  # 允许事件继续传递
    def on_in_label_text(self,event):
        in_currency = self.rates_input_combo.GetValue()
        out_currency = self.rates_output_combo.GetValue()
        in_num = self.rates_input_label.GetValue()

        if out_currency != "" and in_currency != "":
            if in_num == "":
                in_num = '0'
            exchange_thread = threading.Thread(target=self.rates.get_exchange_rate, args=(in_currency, out_currency, int(in_num),self.rates_output_label))
            exchange_thread.start()

    def on_in_combo_select(self, event):
        # 当用户从下拉列表中选择一项时调用
        in_currency = self.rates_input_combo.GetValue()
        out_currency = self.rates_output_combo.GetValue()
        in_num = self.rates_input_label.GetValue()
        if out_currency != "" and in_currency != "":
            if in_num == "":
                in_num = '0'
            exchange_thread = threading.Thread(target=self.rates.get_exchange_rate, args=(in_currency, out_currency, int(in_num),self.rates_output_label))
            exchange_thread.start()
    def on_out_combo_select(self, event):
        # 当用户从下拉列表中选择一项时调用
        in_currency = self.rates_input_combo.GetValue()
        out_currency = self.rates_output_combo.GetValue()
        in_num = self.rates_input_label.GetValue()
        if in_currency == "":
            wx.MessageBox('选择想要计算的货币', '注意', wx.OK | wx.ICON_INFORMATION)
            return
        if in_num == "":
            in_num = '0'
        exchange_thread = threading.Thread(target=self.rates.get_exchange_rate, args=(in_currency, out_currency, int(in_num),self.rates_output_label))
        exchange_thread.start()