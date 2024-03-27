from base64 import b64decode,b64encode
from hashlib import md5
from Crypto.Cipher import AES
from Crypto.Cipher import DES
from Crypto.Util.Padding import pad, unpad

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
