import wx
from base64 import b64decode,b64encode
from hashlib import md5
from Crypto.Cipher import AES
from Crypto.Cipher import DES
from Crypto.Util.Padding import pad, unpad

class AlgorithmPage(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.initUI()
    def initUI(self):
        ### 加解密页面
        # 算法选择相关组件
        self.algorithm_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.algorithm_label = wx.StaticText(self, label="选择算法:")
        self.algorithm_combo = wx.ComboBox(self, choices=["Base64", "MD5", "AES", "DES"], style=wx.CB_READONLY)
        self.algorithm_combo.SetSelection(0) 

        self.encrypt_button = wx.Button(self, label="加密")
        self.decrypt_button = wx.Button(self, label="解密")
        self.algorithm_sizer.Add(self.algorithm_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.algorithm_sizer.Add(self.algorithm_combo, 0,wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)
        self.algorithm_sizer.Add(self.encrypt_button, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)
        self.algorithm_sizer.Add(self.decrypt_button, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        
        # 输入输出文本相关组件
        self.text_sizer  = wx.BoxSizer(wx.HORIZONTAL)
        self.input_sizer = wx.BoxSizer(wx.VERTICAL)
        self.input_label = wx.StaticText(self, label="输入:")
        self.input_text = wx.TextCtrl(self,style = wx.TE_MULTILINE)
        self.input_sizer.Add(self.input_label, 0, wx.ALL, 5)
        self.input_sizer.Add(self.input_text, 1,wx.EXPAND|wx.ALL)

        self.output_sizer = wx.BoxSizer(wx.VERTICAL)
        self.output_label = wx.StaticText(self, label="输出:")
        self.output_text = wx.TextCtrl(self, style = wx.TE_READONLY | wx.TE_MULTILINE)
        self.output_sizer.Add(self.output_label, 0, wx.ALL, 5)
        self.output_sizer.Add(self.output_text, 1, wx.EXPAND|wx.ALL)
        self.text_sizer.Add(self.input_sizer,1, wx.EXPAND|wx.ALL, 10)
        self.text_sizer.Add(self.output_sizer,1, wx.EXPAND|wx.ALL, 10)
        
        # AES/DES加密参数相关组件
        self.mode_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.mode_label = wx.StaticText(self, label="加密模式:")
        self.mode_combo = wx.ComboBox(self, choices=["ECB", "CBC", "CFB", "OFB"], style=wx.CB_READONLY)
        self.mode_combo.SetSelection(0) 

        self.padding_label = wx.StaticText(self, label="填充:")
        self.padding_combo = wx.ComboBox(self, choices=["pkcs7", "x923","iso7816"], style=wx.CB_READONLY)
        self.padding_combo.SetSelection(0) 

        self.key_len_label = wx.StaticText(self, label="秘钥长度:")
        self.key_len_combo = wx.ComboBox(self, choices=["128", "192", "256"], style=wx.CB_READONLY)
        self.key_len_combo.SetSelection(0) 

        self.key_label = wx.StaticText(self, label="秘钥:")
        self.key_text = wx.TextCtrl(self)

        self.iv_label = wx.StaticText(self, label="偏移量:")
        self.iv_text = wx.TextCtrl(self)

        self.out_mode_label = wx.StaticText(self, label="输出格式:")
        self.out_mode_combo = wx.ComboBox(self, choices=["hex"], style=wx.CB_READONLY)
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

        self.SetSizer(self.sizer)

        self.algorithm_combo.Bind(wx.EVT_COMBOBOX, self.on_algorithm_change)
        self.mode_combo.Bind(wx.EVT_COMBOBOX, self.on_mode_change)
        self.encrypt_button.Bind(wx.EVT_BUTTON, self.OnEncrypt)
        self.decrypt_button.Bind(wx.EVT_BUTTON, self.OnDecrypt)

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
        self.Layout()

    def on_mode_change(self, event):
        mode = self.mode_combo.GetValue()
        if mode == "ECB":
            self.iv_label.Hide()
            self.iv_text.Hide()
        else:
            self.iv_label.Show()
            self.iv_text.Show()
        self.Layout()
def base64_encode(text):
    # 将字符串编码为字节流
    byte_data = text.encode('utf-8')
    # 使用Base64进行编码
    encoded_data = b64encode(byte_data)
    # 将字节流转换为字符串
    encoded_text = encoded_data.decode('utf-8')
    return encoded_text

def base64_decode(encoded_text):
    # 将字符串转换为字节流
    byte_data = encoded_text.encode('utf-8')
    # 使用Base64进行解码
    decoded_data = b64decode(byte_data)
    # 将字节流转换为字符串
    decoded_text = decoded_data.decode('utf-8')
    return decoded_text

def md5_encode(text):
    """
    MD5 加密
    :param text: 待加密文本
    :return: 加密后的文本
    """
    m = md5()
    m.update(text.encode('utf-8'))
    return m.hexdigest()

def md5_decode(text):
    """
    MD5 解密
    :param text: 待解密文本
    :return: 解密后的文本
    """
    return "MD5 不支持解密"
def customize_pad(s,BLOCK_SIZE):
    return s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * bytes([0])

def aes_encrypt(key, iv, data, block_size,padding,encrypt_mode):

    if len(key) < block_size:
        key = customize_pad(key, block_size)
    else:
        key = key[:block_size]
    if len(iv) < AES.block_size:
        iv = customize_pad(iv,AES.block_size)
    else:
        iv = iv[:AES.block_size]
    
    # 创建AES加密器"ECB", "CBC", "CFB", "OFB"
    cipher = None
    if encrypt_mode == "ECB":
        cipher = AES.new(key, AES.MODE_ECB)
    elif encrypt_mode == "CBC":
        cipher = AES.new(key, AES.MODE_CBC, iv)
    elif encrypt_mode == "CFB":
        cipher = AES.new(key, AES.MODE_CFB, iv)
    elif encrypt_mode == "OFB":
        cipher = AES.new(key, AES.MODE_OFB, iv)
    
    # 对数据进行填充
    padded_data = pad(data.encode('utf-8'), AES.block_size, style=padding)

    # 加密数据
    ciphertext = cipher.encrypt(padded_data)

    return ciphertext.hex()


def aes_decrypt(key, iv,data, block_size,padding,encrypt_mode):
    if len(key) < block_size:
        key = customize_pad(key, block_size)
    else:
        key = key[:block_size]
    if len(iv) < AES.block_size:
        iv = customize_pad(iv,AES.block_size)
    else:
        iv = iv[:AES.block_size]
    # 创建AES解密器"ECB", "CBC", "CFB", "OFB"
    cipher = None
    if encrypt_mode == "ECB":
        cipher = AES.new(key, AES.MODE_ECB)
    elif encrypt_mode == "CBC":
        cipher = AES.new(key, AES.MODE_CBC, iv)
    elif encrypt_mode == "CFB":
        cipher = AES.new(key, AES.MODE_CFB, iv)
    elif encrypt_mode == "OFB":
        cipher = AES.new(key, AES.MODE_OFB, iv)

    # 解密数据
    decrypted_data = cipher.decrypt(data)

    # 去除填充
    unpadded_data = unpad(decrypted_data, AES.block_size, style=padding)

    return unpadded_data.decode('utf-8')

def des_encrypt(key, iv, data,padding,encrypt_mode):

    if len(key) < DES.block_size:
        key = customize_pad(key, DES.block_size)
    else:
        key = key[:DES.block_size]
    if len(iv) < DES.block_size:
        iv = customize_pad(iv,DES.block_size)
    else:
        iv = iv[:DES.block_size]

    # 创建DES加密器"ECB", "CBC", "CFB", "OFB"
    cipher = None
    if encrypt_mode == "ECB":
        cipher = DES.new(key, DES.MODE_ECB)
    elif encrypt_mode == "CBC":
        cipher = DES.new(key, DES.MODE_CBC, iv)
    elif encrypt_mode == "CFB":
        cipher = DES.new(key, DES.MODE_CFB, iv)
    elif encrypt_mode == "OFB":
        cipher = DES.new(key, DES.MODE_OFB, iv)
    
    # 对数据进行填充
    padded_data = pad(data.encode('utf-8'), DES.block_size, style=padding)

    # 加密数据
    ciphertext = cipher.encrypt(padded_data)

    return ciphertext.hex()


def des_decrypt(key, iv,data,padding,encrypt_mode):
    if len(key) < DES.block_size:
        key = customize_pad(key, DES.block_size)
    else:
        key = key[:DES.block_size]
    if len(iv) < DES.block_size:
        iv = customize_pad(iv,DES.block_size)
    else:
        iv = iv[:DES.block_size]

    # 创建DES加密器"ECB", "CBC", "CFB", "OFB"
    cipher = None
    if encrypt_mode == "ECB":
        cipher = DES.new(key, DES.MODE_ECB)
    elif encrypt_mode == "CBC":
        cipher = DES.new(key, DES.MODE_CBC, iv)
    elif encrypt_mode == "CFB":
        cipher = DES.new(key, DES.MODE_CFB, iv)
    elif encrypt_mode == "OFB":
        cipher = DES.new(key, DES.MODE_OFB, iv)

    # 解密数据
    decrypted_data = cipher.decrypt(data)

    # 去除填充
    unpadded_data = unpad(decrypted_data, DES.block_size, style=padding)

    return unpadded_data.decode('utf-8')
