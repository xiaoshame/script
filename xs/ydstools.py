import xxtea
import struct
import os
import json
import base64

#"yida-123456789"
xxtea_key = bytes([0x79, 0x69, 0x64, 0x61, 0x2d, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39,0x00,0x00])
xxtea_key_password = bytes([0x79, 0x69, 0x64, 0x61, 0x5f, 0x40, 0x23, 0x25, 0x24, 0x21, 0x67, 0x7e, 0x60, 0x73, 0x76, 0x28]) ##, 0x28, 0x2a, 0x26, 0x29, 0x29])
encrypt_marking = bytes.fromhex('406865616465723a7631')
mark = bytes([0xFF,0x80,0x40,0x20,0x10,0x08,0x04])

def yds2json(buffer):
    try:
        if buffer[:10] == encrypt_marking:
            out = xxtea.decrypt(buffer[10:], xxtea_key_password,False, 0)
        else:
            out = xxtea.decrypt(buffer[7:], xxtea_key,False, 0)
    except Exception as e:
        return None, str(e)
    
    n = len(out)
    n -= 4
    m = struct.unpack('<I', out[n:])[0]
    
    if m < n - 3 or m > n:
        return None, "decode error"
    
    n = m
    return out[:n], None

def json2yds(buffer):
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
        # decoded_str = buffer.decode('utf-8')
        # hex_representation = ['0x{:02x}'.format(ord(char)) for char in decoded_str]
        # output_str = ','.join(hex_representation)
        # print(output_str)
        out = xxtea.encrypt(buffer, xxtea_key,False, 0)
        # print(out)
        return out, None
    except Exception as e:
        return None, str(e)
    
def encrypt_json2yds(buffer):
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
        # decoded_str = buffer.decode('utf-8')
        # hex_representation = ['0x{:02x}'.format(ord(char)) for char in decoded_str]
        # output_str = ','.join(hex_representation)
        # print(output_str)
        out = xxtea.encrypt(buffer, xxtea_key_password,False, 0)
        # print(out)
        return out, None
    except Exception as e:
        return None, str(e)

def load_file(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'rb') as file:
            return file.read(),None
    else:
        return None, f"File {filepath} does not exist."

### 书源带密码
def encrypt_yds_to_json(input,output):
    data, error = load_file(input)
    if error:
        print(error)
        exit(1)
    encode_data,error = yds2json(data)
    if error:
        print(error)
        exit(1)
    json_str = encode_data.decode('utf-8')
    parsed_data = json.loads(json_str)
    for key, value in parsed_data.items():
        if 'data' in value:
            data_value = value['data']
            try:
                decoded_data = base64.b64decode(data_value)
            except base64.binascii.Error as e:
                print(f"Error decoding base64 for key {key}: {e}")
                exit(1)
            result,error = yds2json(decoded_data)
            if error:
                print(error)
                exit(1)
            value['data'] = result.decode('utf-8')
    # 打开文件以二进制模式写入
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(parsed_data, f, ensure_ascii=False, indent=4)

def encrypt_json_to_yds(input,output):
    data, error = load_file(input)
    if error:
        print(error)
        exit(1)
    json_str = data.decode('utf-8')
    parsed_data = json.loads(json_str)
    for key, value in parsed_data.items():
        if 'data' in value:
            data_value = value['data']
            result,error = encrypt_json2yds(data_value.encode('utf-8'))
            if error:
                print(error)
                exit(1)
            try:
                encode_data = base64.b64encode(encrypt_marking+result)
            except base64.binascii.Error as e:
                print(f"Error decoding base64 for key {key}: {e}")
                exit(1)
            value['data'] = encode_data.decode('utf-8')
    ## 不加ensure_ascii=False 非ASCII 字符会被转为 Unicode 转义序列
    encode_json = json.dumps(parsed_data, ensure_ascii=False).encode('utf8')

### 过滤空格后可以保证json加密结果与原始数据一样,不是用不影响导入
    # result_data = re.sub(r'\s*:\s*', ':', encode_json)
    # result_data = re.sub(r',\s*', ',', result_data)
    # result_data = re.sub(r'{\s*', '{', result_data)
    # result_data = re.sub(r'\s*}', '}', result_data).encode('utf8')

    result,error = encrypt_json2yds(encode_json)
    if error:
        print(error)
        exit(1)
    with open(output, 'wb') as f:
        f.write(encrypt_marking)
        f.write(result)

### 书源不带密码
def yds_to_json(input,output):
    data, error = load_file(input)
    if error:
        print(error)
        exit(1)
    encode_data,error = yds2json(data)
    if error:
        print(error)
        exit(1)
    # 打开文件以二进制模式写入
    with open(output, 'w', encoding='utf-8') as f:
        json_data = json.loads(encode_data.decode('utf-8'))
        json.dump(json_data, f, ensure_ascii=False, indent=4)
def json_to_yds(input,output):
    data, error = load_file(input)
    if error:
        print(error)
        exit(1)
    decode_data,error = json2yds(data)
    if error:
        print(error)
        exit(1)
    with open(output, 'wb') as f:
        f.write(mark)
        f.write(decode_data)

if __name__ == '__main__':

    encrypt_yds_to_json('D:\\workspace\\script\\xs\\data\\ydSource.yds' , 'D:\\workspace\\script\\xs\\data\\ydSource.json')
    # encrypt_json_to_yds('D:\\workspace\\script\\xs\\data\\1.json' , 'D:\\workspace\\script\\xs\\data\\222.yds')
    # yds_to_json('D:\\workspace\\script\\xs\\data\\bilibili.yds' , 'D:\\workspace\\script\\xs\\data\\bilibili.json')
    # json_to_yds('D:\\workspace\\script\\xs\\data\\bilibili.json' , 'D:\\workspace\\script\\xs\\data\\bilibili_.yds')


    