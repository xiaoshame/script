
import subprocess


def insert_sei(input_file, output_file, sei_data):
    command = [
        'ffmpeg',
        '-i', input_file,
        '-c', 'copy',
        '-bsf:v', f'h264_metadata=sei_user_data={sei_data}',
        output_file
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error inserting SEI data: {result.stderr}")
    else:
        print(f"SEI data inserted successfully into {output_file}")

def extract_sei(input_video: str):
    command = [
        'ffmpeg',
        '-i', input_video,
        '-c', 'copy',
        '-bsf:v', 'trace_headers',
        '-f', 'null', '-'
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    
    # 目前看无法直接通过命令行提取SEI信息，待解决todo
    sei_lines = [line for line in result.stdout.split('\n') if 'sei_user_data' in line]
    return sei_lines


# 使用示例
input_video = 'D:\\workspace\\script\\watermarks\\input.mp4'
output_video = 'D:\\workspace\\script\\watermarks\\output.mp4'
sei_message = '086f3693-b7b3-4f2c-9653-21492feee5b8+123456@'

# 写入SEI数据
insert_sei(input_video, output_video, sei_message)

# # 读取SEI数据
extracted_sei = extract_sei(output_video)
if extracted_sei:
    print(f"提取的SEI信息: {extracted_sei}")
else:
    print("未找到SEI信息")
