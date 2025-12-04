import requests
import re
import json
import time

def clock_in(key,wordpress,wordpress_logged_in):
    template = """%s; PHPSESSID=rbticc4c6fne84qp1obek4tubb; wordpress_test_cookie=WP+Cookie+check; %s; cao_notice_cookie=1"""
    cookie = template % (wordpress,wordpress_logged_in)

    url = 'https://www.huaxiashuyu.com/wp-admin/admin-ajax.php'
    headers = {
        'authority': 'www.huaxiashuyu.com',
        'accept': '*/*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'cookie': cookie,
        'origin': 'https://www.huaxiashuyu.com',
        'pragma': 'no-cache',
        'referer': 'https://www.huaxiashuyu.com/',
        'sec-ch-ua': '"Microsoft Edge";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
        'x-requested-with': 'XMLHttpRequest',
    }

    data = {
        'action': 'user_qiandao',
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        json_data = json.loads(response.content.decode('utf-8'))
        msg = json_data['msg']
        QLAPI.systemNotify({"title": "花夏数娱打卡: " + key, "content": msg})

def sign_up(name,password):
    url = "https://www.huaxiashuyu.com/wp-admin/admin-ajax.php"
    
    template = """action=user_login&username=%s&password=%s"""

    payload  = template % (name,password)

    headers = {
    'authority': 'www.huaxiashuyu.com',
    'accept': '*/*',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'cache-control': 'no-cache',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'cookie': 'cao_notice_cookie=1; PHPSESSID=rbticc4c6fne84qp1obek4tubb; wordpress_test_cookie=WP+Cookie+check',
    'origin': 'https://www.huaxiashuyu.com',
    'pragma': 'no-cache',
    'referer': 'https://www.huaxiashuyu.com/',
    'sec-ch-ua': '"Microsoft Edge";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
    'x-requested-with': 'XMLHttpRequest'
    }
    wordpress = wordpress_logged_in = ''
    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 200:
        print(json.loads(response.content.decode('utf-8')))
        cookies = response.cookies
        for cookie in cookies:
            if re.search(r"wordpress_logged_in", cookie.name):
                wordpress_logged_in = cookie.name + '=' + cookie.value
            else:
                wordpress = cookie.name + '=' + cookie.value
        return wordpress,wordpress_logged_in
    else:
        return wordpress,wordpress_logged_in


if __name__ == "__main__":
    accounts = {'':'','':'','':''}
    for key, value in accounts.items():
        wordpress,wordpress_logged_in = sign_up(key,value)
        clock_in(key,wordpress,wordpress_logged_in)
        time.sleep(60)
