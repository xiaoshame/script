import json
import requests
from requests.exceptions import RequestException
from concurrent.futures import ThreadPoolExecutor, as_completed

def is_url_available(url, proxies=None):
    """
    检查URL是否可用。
    如果URL可用，返回True；否则返回False。
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    try:
        response = requests.head(url, timeout=10, proxies=proxies, headers=headers, allow_redirects=True, verify=True)
        # 检查多种成功状态码
        return response.status_code in [200, 301, 302, 307, 308,403]
    except RequestException as e:
        print(f"Error checking URL {url}: {e}")
        return False

def process_entry(entry, proxies):
    """
    处理单个条目，检查URL是否可用。
    """
    url = entry.get('sourceUrl')
    if is_url_available(url, proxies):
        return entry
    return None

if __name__ == '__main__':
    # 配置代理
    proxies = {
        'http': 'http://127.0.0.1:1081',
        'https': 'http://127.0.0.1:1081'
    }
    # 读取JSON文件
    with open('D:\\workspace\\script\\xs\\data\\919.json', 'r',encoding='utf-8') as file:
        data = json.load(file)
    entries_list = list(data.items())
    total_entries = len(entries_list)
    available_entries = {}
    invalid_url_count = 0
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_entry = {executor.submit(process_entry, entry, proxies): (key, entry) for key, entry in entries_list}
        completed_count = 0
        for future in as_completed(future_to_entry):
            result = future.result()
            if result:
                key, entry = future_to_entry[future]
                available_entries[key] = entry
            else:
                invalid_url_count += 1
            completed_count += 1
            print(f"Progress: {completed_count}/{total_entries} ({(completed_count / total_entries) * 100:.2f}%), Invalid URLs: {invalid_url_count}")
    # 将可用的json 保存到新的文件中
    with open("D:\\workspace\\script\\xs\\data\\919_new.json", "w",encoding='utf-8') as f:
        json.dump(available_entries, f, ensure_ascii=False, indent=4)

