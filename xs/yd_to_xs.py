
import requests

def get_yd_json(url):
    response = requests.get(url, headers=headers)

if __name__ == "__main__":
    get_yd_json('https://jt12.de/SYV2_4/2023/08/06/10/11/23/169128788364cf014b941ad.json')