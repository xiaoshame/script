import xxtea
import struct
import os
import json


xxtea_key = bytes([0xe5, 0x87, 0xbc, 0xe8, 0xa4, 0x86, 0xe6, 0xbb, 0xbf, 0xe9, 0x87, 0x91, 0xe6, 0xba, 0xa1, 0xe5])

def xbs2json(buffer):

    try:
        out = xxtea.decrypt(buffer, xxtea_key,False, 0)
    except Exception as e:
        return None, str(e)
    
    n = len(buffer)
    n -= 4
    m = struct.unpack('<I', out[n:])[0]
    
    if m < n - 3 or m > n:
        return None, "decode error"
    
    n = m
    return out[:n], None

def json2xbs(buffer):
    buffer_len = len(buffer)
    n = buffer_len // 4
    if buffer_len % 4 != 0:
        n += 1
    
    # Pad the buffer to the next multiple of 4
    padding_length = n * 4 - buffer_len
    buffer_enc_len = b'\x00' * padding_length
    
    # Append the original buffer length as a little-endian uint32
    buffer_enc_len += struct.pack('<I', buffer_len)
    
    # Combine the original buffer with the padding and length
    buffer = buffer + buffer_enc_len
    
    try:
        # Encrypt the buffer using XXTEA
        out = xxtea.encrypt(buffer, xxtea_key,False, 0)
        return out, None
    except Exception as e:
        return None, str(e)

def load_file(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'rb') as file:
            return file.read(),None
    else:
        return None, f"File {filepath} does not exist."

def xbs_to_json(input,output):
    data, error = load_file(input)
    if error:
        print(error)
        exit(1)
    encode_data,error = xbs2json(data)
    if error:
        print(error)
        exit(1)
    # 打开文件以二进制模式写入
    with open(output, 'w', encoding='utf-8') as f:
        json_data = json.loads(encode_data.decode('utf-8'))
        json.dump(json_data, f, ensure_ascii=False, indent=4)
def json_to_xbs(input,output):
    data, error = load_file(input)
    if error:
        print(error)
        exit(1)
    decode_data,error = json2xbs(data)
    if error:
        print(error)
        exit(1)
    with open(output, 'wb') as f:
        f.write(decode_data)

if __name__ == '__main__':
    # xbs_to_json('D:\\workspace\\script\\xs\\data\\sourceModelList.xbs' , 'D:\\workspace\\script\\xs\\data\\sourceModelList.json')
    json_to_xbs('D:\\workspace\\script\\xs\\data\\sourceModelList.json' , 'D:\\workspace\\script\\xs\\data\\sourceModelList.xbs')