import requests
from wx import CallAfter

class MyRates:
    # 初始化方法
    def __init__(self):
        self.my_rates_dict = {}

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
                    rates = data["conversion_rates"][rates_currency]
                    self.my_rates_dict[base_currency+'-'+rates_currency] = rates
                    CallAfter(control.SetLabel,str(rates * num))
                return r.status_code
            except Exception as e:
                print(e)
                return 0