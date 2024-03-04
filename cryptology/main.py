import wx
from datetime import datetime
from mytime import timestamp_to_datetime,datetime_to_timestamp
from mycrypt import des_decrypt,aes_decrypt,md5_decode,base64_decode,des_encrypt,aes_encrypt,md5_encode,base64_encode

class EncryptionFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="常用工具", size=(820, 500))
        # self.app_icon = wx.Icon('favicon.ico', wx.BITMAP_TYPE_ICO)
        # self.SetIcon(self.app_icon)

        self.panel = wx.Panel(self)

        self.notebook = wx.Notebook(self.panel)

        self.algorithm_table = wx.Panel(self.notebook)
        self.time_table = wx.Panel(self.notebook)
        self.format_table = wx.Panel(self.notebook)

        ### 加解密页面
        # 算法选择相关组件
        self.algorithm_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.algorithm_label = wx.StaticText(self.algorithm_table, label="选择算法:")
        self.algorithm_combo = wx.ComboBox(self.algorithm_table, choices=["Base64", "MD5", "AES", "DES"], style=wx.CB_READONLY)
        self.algorithm_combo.SetSelection(0) 

        self.encrypt_button = wx.Button(self.algorithm_table, label="加密")
        self.decrypt_button = wx.Button(self.algorithm_table, label="解密")
        self.algorithm_sizer.Add(self.algorithm_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.algorithm_sizer.Add(self.algorithm_combo, 0,wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)
        self.algorithm_sizer.Add(self.encrypt_button, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)
        self.algorithm_sizer.Add(self.decrypt_button, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        
        # 输入输出文本相关组件
        self.text_sizer  = wx.BoxSizer(wx.HORIZONTAL)
        self.input_sizer = wx.BoxSizer(wx.VERTICAL)
        self.input_label = wx.StaticText(self.algorithm_table, label="输入:")
        self.input_text = wx.TextCtrl(self.algorithm_table,style = wx.TE_MULTILINE)
        self.input_sizer.Add(self.input_label, 0, wx.ALL, 5)
        self.input_sizer.Add(self.input_text, 1,wx.EXPAND|wx.ALL)

        self.output_sizer = wx.BoxSizer(wx.VERTICAL)
        self.output_label = wx.StaticText(self.algorithm_table, label="输出:")
        self.output_text = wx.TextCtrl(self.algorithm_table, style = wx.TE_READONLY | wx.TE_MULTILINE)
        self.output_sizer.Add(self.output_label, 0, wx.ALL, 5)
        self.output_sizer.Add(self.output_text, 1, wx.EXPAND|wx.ALL)
        self.text_sizer.Add(self.input_sizer,1, wx.EXPAND|wx.ALL, 10)
        self.text_sizer.Add(self.output_sizer,1, wx.EXPAND|wx.ALL, 10)
        
        # AES/DES加密参数相关组件
        self.mode_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.mode_label = wx.StaticText(self.algorithm_table, label="加密模式:")
        self.mode_combo = wx.ComboBox(self.algorithm_table, choices=["ECB", "CBC", "CFB", "OFB"], style=wx.CB_READONLY)
        self.mode_combo.SetSelection(0) 

        self.padding_label = wx.StaticText(self.algorithm_table, label="填充:")
        self.padding_combo = wx.ComboBox(self.algorithm_table, choices=["pkcs7", "x923","iso7816"], style=wx.CB_READONLY)
        self.padding_combo.SetSelection(0) 

        self.key_len_label = wx.StaticText(self.algorithm_table, label="秘钥长度:")
        self.key_len_combo = wx.ComboBox(self.algorithm_table, choices=["128", "192", "256"], style=wx.CB_READONLY)
        self.key_len_combo.SetSelection(0) 

        self.key_label = wx.StaticText(self.algorithm_table, label="秘钥:")
        self.key_text = wx.TextCtrl(self.algorithm_table)

        self.iv_label = wx.StaticText(self.algorithm_table, label="偏移量:")
        self.iv_text = wx.TextCtrl(self.algorithm_table)

        self.out_mode_label = wx.StaticText(self.algorithm_table, label="输出格式:")
        self.out_mode_combo = wx.ComboBox(self.algorithm_table, choices=["hex"], style=wx.CB_READONLY)
        self.out_mode_combo.SetSelection(0)

        self.mode_sizer.Add(self.mode_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.mode_sizer.Add(self.mode_combo, 0, wx.ALIGN_CENTER_VERTICAL, 5)
        self.mode_sizer.Add(self.padding_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.mode_sizer.Add(self.padding_combo, 0, wx.ALIGN_CENTER_VERTICAL, 5)

        self.mode_sizer.Add(self.key_len_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.mode_sizer.Add(self.key_len_combo, 0, wx.ALIGN_CENTER_VERTICAL, 5)
        self.mode_sizer.Add(self.key_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.mode_sizer.Add(self.key_text, 0, wx.ALIGN_CENTER_VERTICAL, 5)
        self.mode_sizer.Add(self.iv_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.mode_sizer.Add(self.iv_text, 0, wx.ALIGN_CENTER_VERTICAL, 5)

        self.mode_sizer.Add(self.out_mode_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.mode_sizer.Add(self.out_mode_combo, 0, wx.ALIGN_CENTER_VERTICAL, 5)
        for item in self.mode_sizer.GetChildren():
            window = item.GetWindow()
            if window:  # 如果item是一个窗口
                window.Hide()

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.algorithm_sizer, 0, wx.EXPAND|wx.ALL, 5)
        self.sizer.Add(self.mode_sizer, 0, wx.EXPAND|wx.ALL, 5)
        self.sizer.Add(self.text_sizer, 1, wx.ALL|wx.EXPAND, 5)

        self.algorithm_table.SetSizer(self.sizer)

        ### 时间戳页面
        self.timestamp_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.timestamp_label = wx.StaticText(self.time_table, label="时间戳:")
        self.timestamp_input_text = wx.TextCtrl(self.time_table)
        self.timestamp_button = wx.Button(self.time_table, label="转换")
        self.timestamp_output_text = wx.TextCtrl(self.time_table)

        self.timestamp_sizer.Add(self.timestamp_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.timestamp_sizer.Add(self.timestamp_input_text, 1,wx.EXPAND|wx.ALL, 5)
        self.timestamp_sizer.Add(self.timestamp_button, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.timestamp_sizer.Add(self.timestamp_output_text, 1, wx.EXPAND|wx.ALL, 5)

        self.timing_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.timing_label = wx.StaticText(self.time_table, label="时间:")
        self.timing_input_text = wx.TextCtrl(self.time_table)
        self.timing_button = wx.Button(self.time_table, label="转换")
        self.timing_output_text = wx.TextCtrl(self.time_table)

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
        self.time_table.SetSizer(self.time_sizer)

        ### 格式化页面


        self.notebook.AddPage(self.algorithm_table, "加解密")
        self.notebook.AddPage(self.time_table, "时间戳")
        self.notebook.AddPage(self.format_table,"格式化")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.EXPAND)
        self.panel.SetSizer(sizer)

        self.algorithm_combo.Bind(wx.EVT_COMBOBOX, self.on_algorithm_change)
        self.mode_combo.Bind(wx.EVT_COMBOBOX, self.on_mode_change)
        self.encrypt_button.Bind(wx.EVT_BUTTON, self.OnEncrypt)
        self.decrypt_button.Bind(wx.EVT_BUTTON, self.OnDecrypt)
        self.timestamp_button.Bind(wx.EVT_BUTTON, self.OnTimestamp)
        self.timing_button.Bind(wx.EVT_BUTTON, self.OnTiming)

        self.Show()

        
    def OnEncrypt(self, event):
        self.output_text.SetValue("")
        algorithm = self.algorithm_combo.GetValue()
        input_text = self.input_text.GetValue()
        
        # 根据选择的算法进行加密操作
        if algorithm == "Base64":
            encrypted_text = base64_encode(input_text)
        elif algorithm == "MD5":
            encrypted_text = md5_encode(input_text)
        elif algorithm == "AES":
            encrypt_mode = self.mode_combo.GetValue()
            key_text = self.key_text.GetValue()
            key_len = self.key_len_combo.GetValue()
            iv_text = self.iv_text.GetValue()
            padding= self.padding_combo.GetValue()
            encrypted_text = aes_encrypt(key_text.encode('utf-8'),iv_text.encode('utf-8'),input_text,int(int(key_len)/8),padding,encrypt_mode)
        elif algorithm == "RSA":
            encrypted_text = aes_encrypt(input_text)
        elif algorithm == "DES":
            encrypt_mode = self.mode_combo.GetValue()
            key_text = self.key_text.GetValue()
            key_len = self.key_len_combo.GetValue()
            iv_text = self.iv_text.GetValue()
            padding= self.padding_combo.GetValue()
            encrypted_text = des_encrypt(key_text.encode('utf-8'),iv_text.encode('utf-8'),input_text,padding,encrypt_mode)
        else:
            encrypted_text = "请选择算法"
        
        self.output_text.SetValue(encrypted_text)
    
    def OnDecrypt(self, event):
        self.output_text.SetValue("")
        algorithm = self.algorithm_combo.GetValue()
        input_text = self.input_text.GetValue()
        
        # 根据选择的算法进行解密操作
        if algorithm == "Base64":
            decrypted_text = base64_decode(input_text)
        elif algorithm == "MD5":
            decrypted_text = md5_decode(input_text)
        elif algorithm == "AES":
            key_text = self.key_text.GetValue()
            encrypt_mode = self.mode_combo.GetValue()           
            key_len = self.key_len_combo.GetValue()
            iv_text = self.iv_text.GetValue()
            padding= self.padding_combo.GetValue()
            decrypted_text = aes_decrypt(key_text.encode('utf-8'),iv_text.encode('utf-8'),bytes.fromhex(input_text),int(int(key_len)/8),padding,encrypt_mode)
        elif algorithm == "RSA":
            decrypted_text = aes_decrypt(input_text)
        elif algorithm == "DES":
            key_text = self.key_text.GetValue()
            encrypt_mode = self.mode_combo.GetValue()           
            key_len = self.key_len_combo.GetValue()
            iv_text = self.iv_text.GetValue()
            padding= self.padding_combo.GetValue()
            decrypted_text = des_decrypt(key_text.encode('utf-8'),iv_text.encode('utf-8'),bytes.fromhex(input_text),padding,encrypt_mode)
        else:
            decrypted_text = "请选择算法"        
        self.output_text.SetValue(decrypted_text)

    def on_algorithm_change(self, event):
        algorithm = self.algorithm_combo.GetValue()
        if algorithm in ["AES","DES"]:
            for item in self.mode_sizer.GetChildren():
                window = item.GetWindow()
                if window:  # 如果item是一个窗口
                    window.Show()
            if self.mode_combo.GetValue() == "ECB":
                self.iv_label.Hide()
                self.iv_text.Hide()
            if algorithm == "DES":
                self.key_len_combo.Hide()
                self.key_len_label.Hide()
        elif algorithm == "RSA":
            for item in self.mode_sizer.GetChildren():
                window = item.GetWindow()
                if window: # 如果item是一个窗口
                    window.Show()
            self.iv_label.Hide()
            self.iv_text.Hide()
        else:
            for item in self.mode_sizer.GetChildren():
                window = item.GetWindow()
                if window:  # 如果item是一个窗口
                    window.Hide()
        self.algorithm_table.Layout()

    def on_mode_change(self, event):
        mode = self.mode_combo.GetValue()
        if mode == "ECB":
            self.iv_label.Hide()
            self.iv_text.Hide()
        else:
            self.iv_label.Show()
            self.iv_text.Show()
        self.algorithm_table.Layout()

    def OnTimestamp(self, event):
        timestamp_input = self.timestamp_input_text.GetValue()
        datatime_output = timestamp_to_datetime(timestamp_input)
        self.timestamp_output_text.SetValue(datatime_output)

    def OnTiming(self,event):
        timing_input = self.timing_input_text.GetValue()
        timing_output = datetime_to_timestamp(timing_input)
        self.timing_output_text.SetValue(str(timing_output))

if __name__ == "__main__":
    app = wx.App()
    frame = EncryptionFrame()
    frame.Show()
    app.MainLoop()