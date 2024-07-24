import numpy as np
import wave

def encode_watermark(watermark_data, bits_per_sample):
    """
    将水印数据编码为二进制位数组，每个样本使用bits_per_sample位。
    """
    # 假设watermark_data是一个字符串，我们首先将其转换为字节数组
    # 然后，将字节数组转换为二进制位数组
    watermark_bits = []
    for byte in watermark_data.encode('utf-8'):
        for _ in range(8):
            watermark_bits.append(byte & 1)
            byte >>= 1
    
    # 截断或填充以匹配所需的位数（如果需要）
    # 这里我们简化处理，假设watermark_bits长度合适
    return watermark_bits

def decode_watermark(watermark_bits, bits_per_sample):
    """
    将二进制位数组解码为水印数据字符串，假设每个样本使用bits_per_sample位（但在此函数中我们忽略这个参数，因为解码时不需要知道这个信息）。
    """
    # 忽略bits_per_sample参数，因为我们假设watermark_bits已经具有正确的长度
    # 初始化一个空的字节列表
    bytes_list = []
    for i in range(0, len(watermark_bits), 8):
        byte_value = 0
        for j in range(8):
            if i + j < len(watermark_bits):
                byte_value |= watermark_bits[i + j] << (j)
        bytes_list.append(byte_value)
    
    # 将字节列表解码为字符串
    return bytes(bytes_list).decode('utf-8')

def embed_watermark(audio_file, watermark_data, output_file, bits_per_sample=1):
    """
    将水印嵌入到音频文件中。
    
    :param audio_file: 输入音频文件名
    :param watermark_data: 要嵌入的水印数据（字符串）
    :param output_file: 输出音频文件名
    :param bits_per_sample: 每个音频样本中用于水印的位数（默认为1）
    """
    # 读取音频文件
    with wave.open(audio_file, 'rb') as wav_file:
        n_channels, sample_width, framerate, nframes = wav_file.getparams()[:4]
        
        # 假设音频是单声道的
        if n_channels != 1:
            raise ValueError("Audio must be mono channel.")
        
        # 读取音频数据
        audio_data = np.frombuffer(wav_file.readframes(nframes), dtype=np.int16)
        
        # 编码水印数据
        watermark_bits = encode_watermark(watermark_data, bits_per_sample * len(audio_data))
        
        # 如果水印位数超过音频样本数，则截断水印
        if len(watermark_bits) > len(audio_data) * bits_per_sample:
            watermark_bits = watermark_bits[:len(audio_data) * bits_per_sample]
        audio_data_copy = audio_data.copy()
        # 嵌入水印
        for i, sample in enumerate(audio_data):
            # 获取当前样本的最低有效位（或几位）
            lsb_mask = (1 << bits_per_sample) - 1
            original_lsb = sample & lsb_mask
            
            # 计算要嵌入的水印位
            if(i * bits_per_sample >= len(watermark_bits)):
                watermark_bit = 0
            else:
                watermark_bit = watermark_bits[i * bits_per_sample]
            watermark_bits_to_embed = (original_lsb & ~lsb_mask) | (watermark_bit << (bits_per_sample - 1))
            
            # 更新样本的最低有效位
            audio_data_copy[i] = (sample & ~lsb_mask) | watermark_bits_to_embed
        
        # 将处理后的音频数据保存为文件
        with wave.open(output_file, 'wb') as output_wav:
            output_wav.setnchannels(n_channels)
            output_wav.setsampwidth(sample_width)
            output_wav.setframerate(framerate)
            output_wav.writeframes(audio_data_copy.astype(np.int16).tobytes())

def extract_watermark(audio_file, bits_per_sample=1):
    """
    从音频文件中提取水印。
    
    :param audio_file: 包含水印的音频文件名
    :param bits_per_sample: 每个音频样本中用于水印的位数（默认为1）
    :return: 提取的水印数据（字符串）
    """
    # 读取音频文件
    with wave.open(audio_file, 'rb') as wav_file:
        n_channels, sample_width, framerate, nframes = wav_file.getparams()[:4]
        
        # 假设音频是单声道的
        if n_channels != 1:
            raise ValueError("Audio must be mono channel.")
        
        # 读取音频数据
        audio_data = np.frombuffer(wav_file.readframes(nframes), dtype=np.int16)
        
        # 初始化提取的水印位数组
        watermark_bits = []
        
        # 遍历音频样本以提取水印位
        for sample in audio_data:
            # 获取当前样本的最低有效位（或几位）
            lsb_mask = (1 << bits_per_sample) - 1
            watermark_bit = (sample & lsb_mask) >> (bits_per_sample - 1)  # 提取最低位
            watermark_bits.append(watermark_bit)
        
        watermark_data = decode_watermark(watermark_bits, bits_per_sample)
        
        return watermark_data

# 使用示例
watermark_data = "douyu@yyf"  # 要嵌入的水印数据
audio_file = "D:\\workspace\\script\\watermarks\\100024_10.wav"  # 输入音频文件名
output_file = "D:\\workspace\\script\\watermarks\\watermarked.wav"  # 输出音频文件名
embed_watermark(audio_file, watermark_data, output_file, bits_per_sample=1)
extracted_watermark = extract_watermark(output_file, bits_per_sample=1)
print("Extracted watermark:", extracted_watermark)