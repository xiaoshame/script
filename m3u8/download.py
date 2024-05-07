import requests
import subprocess


def download_m3u8_video(url, output_file):
    # 下载m3u8文件
    response = requests.get(url)
    m3u8_content = response.text

    # 解析出所有的视频片段链接
    segments = []
    lines = m3u8_content.split("\n")
    for line in lines:
        if line and not line.startswith("#"):
            segments.append(line.strip())

    # 逐个下载视频片段并保存为ts文件
    ts_files = []
    for i, segment in enumerate(segments):
        response = requests.get(
            "https://play-tx-ugcpub.douyucdn2.cn/live/normal_48754390920230728162906-upload-4f6c/"+segment)
        ts_filename = f"segment_{i}.ts"
        with open(ts_filename, "wb") as f:
            f.write(response.content)
        ts_files.append(ts_filename)

    # 使用ffmpeg将ts文件合并成一个完整的视频文件
    subprocess.run(['ffmpeg', '-i', 'concat:' +
                   '|'.join(ts_files), '-c', 'copy', output_file])

    # # 删除临时生成的ts文件
    # for ts_file in ts_files:
    #     subprocess.run(['del', ts_file])


# 示例用法
m3u8_url = "https://play-tx-ugcpub.douyucdn2.cn/live/normal_48754390920230728162906-upload-4f6c/playlist.m3u8?tlink=64cb5a90&tplay=64cbe730&exper=0&nlimit=5&us=a1a31791bfeb6dabc0e988e9dac7476f&sign=9b1417d467acd0514266b9bb2a8598be&u=0&d=a1a31791bfeb6dabc0e988e9dac7476f&ct=&vid=45147130&pt=1&cdn=tx"
output_file = "output.mp4"
download_m3u8_video(m3u8_url, output_file)
