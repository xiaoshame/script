from wx import CallAfter
import requests
import configparser

class Rates:
    def __init__(self):
        self.my_rates_dict = {}
        # 创建ConfigParser对象
        # 从配置文件读取初始选项列表
        config = configparser.ConfigParser()
        config.read('./config.ini', encoding='utf-8')
        currency_choices_str = config.get('CurrencyNames', 'currency_choices')
        self.currency_choices = [item.strip() for item in currency_choices_str.split(',')]
    def get_exchange_rate(self,input,output,num,control):
        base_currency = input.split("(")[0]
        rates_currency = output.split("(")[0]
        if self.my_rates_dict.get(base_currency+'-'+rates_currency):
            CallAfter(control.SetLabel,str(self.my_rates_dict[base_currency+'-'+rates_currency] * num))
            return
        else:
            api_url='https://v6.exchangerate-api.com/v6/4b9dbf86d6d238d2526c04d4/latest/'+base_currency
            try:
                r=requests.get(api_url)
                if r.status_code==200:
                    data=r.json()
                    for currency,rate in data["conversion_rates"].items():
                        self.my_rates_dict[base_currency+'-'+ currency] = rate
                    rates = data["conversion_rates"][rates_currency]
                    CallAfter(control.SetLabel,str(rates * num))
                return r.status_code
            except Exception as e:
                print(e)
                return 0