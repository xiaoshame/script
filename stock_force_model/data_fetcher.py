# -*- coding: utf-8 -*-
"""
实时数据获取模块

获取股票/指数/行业的实时市值和价格数据
支持多种数据源：
- 东方财富
- 新浪财经
- 腾讯财经
"""

import requests
import json
import re
from datetime import datetime
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
import time


@dataclass
class StockQuote:
    """股票实时行情"""
    symbol: str           # 代码
    name: str             # 名称
    price: float          # 当前价格
    change: float         # 涨跌额
    change_pct: float     # 涨跌幅
    volume: float         # 成交量（手）
    amount: float         # 成交额（元）
    market_cap: float     # 总市值（亿元）
    float_cap: float      # 流通市值（亿元）
    pe_ratio: float       # 市盈率
    pb_ratio: float       # 市净率
    update_time: datetime # 更新时间
    
    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "price": self.price,
            "change": self.change,
            "change_pct": self.change_pct,
            "volume": self.volume,
            "amount": self.amount,
            "market_cap": self.market_cap,
            "float_cap": self.float_cap,
            "pe_ratio": self.pe_ratio,
            "pb_ratio": self.pb_ratio,
            "update_time": self.update_time.isoformat()
        }


class StockDataFetcher:
    """
    股票数据获取器
    
    支持获取A股、港股、指数的实时行情
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://finance.sina.com.cn'
        })
        
        # 缓存
        self._cache: Dict[str, Tuple[StockQuote, float]] = {}
        self._cache_ttl = 60  # 缓存60秒
    
    def _get_market_prefix(self, symbol: str) -> str:
        """
        根据股票代码判断市场
        
        Args:
            symbol: 股票代码
            
        Returns:
            市场前缀 (sh/sz/hk)
        """
        if symbol.startswith('6') or symbol.startswith('5'):
            return 'sh'
        elif symbol.startswith('0') or symbol.startswith('3'):
            return 'sz'
        elif symbol.startswith('BK'):
            return 'bk'  # 板块
        else:
            return 'sh'
    
    def get_quote_sina(self, symbol: str) -> Optional[StockQuote]:
        """
        从新浪获取实时行情
        
        Args:
            symbol: 股票代码
            
        Returns:
            StockQuote 或 None
        """
        try:
            # 检查缓存
            cache_key = f"sina_{symbol}"
            if cache_key in self._cache:
                quote, timestamp = self._cache[cache_key]
                if time.time() - timestamp < self._cache_ttl:
                    return quote
            
            market = self._get_market_prefix(symbol)
            url = f"http://hq.sinajs.cn/list={market}{symbol}"
            
            response = self.session.get(url, timeout=5)
            response.encoding = 'gbk'
            
            # 解析返回数据
            # var hq_str_sh600519="贵州茅台,1800.00,1795.00,1810.00,1820.00,1790.00,..."
            match = re.search(r'"(.+)"', response.text)
            if not match:
                return None
            
            data = match.group(1).split(',')
            if len(data) < 32:
                return None
            
            name = data[0]
            open_price = float(data[1]) if data[1] else 0
            pre_close = float(data[2]) if data[2] else 0
            price = float(data[3]) if data[3] else 0
            high = float(data[4]) if data[4] else 0
            low = float(data[5]) if data[5] else 0
            volume = float(data[8]) if data[8] else 0  # 成交量（股）
            amount = float(data[9]) if data[9] else 0  # 成交额（元）
            
            change = price - pre_close if pre_close > 0 else 0
            change_pct = (change / pre_close * 100) if pre_close > 0 else 0
            
            quote = StockQuote(
                symbol=symbol,
                name=name,
                price=price,
                change=change,
                change_pct=change_pct,
                volume=volume / 100,  # 转换为手
                amount=amount,
                market_cap=0,  # 新浪接口不返回市值
                float_cap=0,
                pe_ratio=0,
                pb_ratio=0,
                update_time=datetime.now()
            )
            
            # 更新缓存
            self._cache[cache_key] = (quote, time.time())
            
            return quote
            
        except Exception as e:
            print(f"[get_quote_sina] Error: {e}")
            return None
    
    def get_quote_eastmoney(self, symbol: str) -> Optional[StockQuote]:
        """
        从东方财富获取实时行情（包含市值）
        
        Args:
            symbol: 股票代码
            
        Returns:
            StockQuote 或 None
        """
        try:
            # 检查缓存
            cache_key = f"em_{symbol}"
            if cache_key in self._cache:
                quote, timestamp = self._cache[cache_key]
                if time.time() - timestamp < self._cache_ttl:
                    return quote
            
            # 判断市场
            if symbol.startswith('6'):
                secid = f"1.{symbol}"
            elif symbol.startswith('0') or symbol.startswith('3'):
                secid = f"0.{symbol}"
            elif symbol.startswith('BK'):
                # 板块指数
                secid = f"90.{symbol}"
            else:
                secid = f"1.{symbol}"
            
            url = "http://push2.eastmoney.com/api/qt/stock/get"
            params = {
                "secid": secid,
                "fields": "f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f57,f58,f60,f116,f117,f162,f167",
                "ut": "fa5fd1943c7b386f172d6893dbfba10b"
            }
            
            response = self.session.get(url, params=params, timeout=5)
            data = response.json()
            
            if 'data' not in data or data['data'] is None:
                return None
            
            d = data['data']
            
            # 解析数据
            price = d.get('f43', 0) / 100 if d.get('f43') else 0
            pre_close = d.get('f60', 0) / 100 if d.get('f60') else 0
            change = price - pre_close
            change_pct = (change / pre_close * 100) if pre_close > 0 else 0
            
            # 市值（单位：元，转换为亿元）
            market_cap = d.get('f116', 0) / 100000000 if d.get('f116') else 0
            float_cap = d.get('f117', 0) / 100000000 if d.get('f117') else 0
            
            quote = StockQuote(
                symbol=symbol,
                name=d.get('f58', ''),
                price=price,
                change=change,
                change_pct=change_pct,
                volume=d.get('f47', 0) / 100 if d.get('f47') else 0,  # 手
                amount=d.get('f48', 0) if d.get('f48') else 0,
                market_cap=market_cap,
                float_cap=float_cap,
                pe_ratio=d.get('f162', 0) / 100 if d.get('f162') else 0,
                pb_ratio=d.get('f167', 0) / 100 if d.get('f167') else 0,
                update_time=datetime.now()
            )
            
            # 更新缓存
            self._cache[cache_key] = (quote, time.time())
            
            return quote
            
        except Exception as e:
            print(f"[get_quote_eastmoney] Error: {e}")
            return None
    
    def get_index_quote(self, symbol: str) -> Optional[StockQuote]:
        """
        获取指数行情
        
        Args:
            symbol: 指数代码 (000001=上证, 399001=深证, 399006=创业板)
            
        Returns:
            StockQuote 或 None
        """
        try:
            # 指数使用不同的secid
            if symbol == '000001':
                secid = "1.000001"
                name = "上证指数"
            elif symbol == '399001':
                secid = "0.399001"
                name = "深证成指"
            elif symbol == '399006':
                secid = "0.399006"
                name = "创业板指"
            elif symbol == '000300':
                secid = "1.000300"
                name = "沪深300"
            else:
                secid = f"1.{symbol}"
                name = ""
            
            url = "http://push2.eastmoney.com/api/qt/stock/get"
            params = {
                "secid": secid,
                "fields": "f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f57,f58,f60,f116",
                "ut": "fa5fd1943c7b386f172d6893dbfba10b"
            }
            
            response = self.session.get(url, params=params, timeout=5)
            data = response.json()
            
            if 'data' not in data or data['data'] is None:
                return None
            
            d = data['data']
            
            price = d.get('f43', 0) / 100 if d.get('f43') else 0
            pre_close = d.get('f60', 0) / 100 if d.get('f60') else 0
            change = price - pre_close
            change_pct = (change / pre_close * 100) if pre_close > 0 else 0
            
            # 指数的"市值"可以理解为成分股总市值
            market_cap = d.get('f116', 0) / 100000000 if d.get('f116') else 0
            
            return StockQuote(
                symbol=symbol,
                name=d.get('f58', name),
                price=price,
                change=change,
                change_pct=change_pct,
                volume=d.get('f47', 0) / 100 if d.get('f47') else 0,
                amount=d.get('f48', 0) if d.get('f48') else 0,
                market_cap=market_cap if market_cap > 0 else self._estimate_index_cap(symbol),
                float_cap=0,
                pe_ratio=0,
                pb_ratio=0,
                update_time=datetime.now()
            )
            
        except Exception as e:
            print(f"[get_index_quote] Error: {e}")
            return None
    
    def _estimate_index_cap(self, symbol: str) -> float:
        """
        估算指数市值（当API无法获取时使用）
        
        Args:
            symbol: 指数代码
            
        Returns:
            估算市值（亿元）
        """
        # 根据历史数据估算
        estimates = {
            '000001': 500000,   # 上证指数约50万亿
            '399001': 300000,   # 深证成指约30万亿
            '000300': 450000,   # 沪深300约45万亿
            '399006': 100000,   # 创业板指约10万亿
        }
        return estimates.get(symbol, 100000)
    
    def get_sector_quote(self, sector_code: str) -> Optional[StockQuote]:
        """
        获取板块行情
        
        Args:
            sector_code: 板块代码 (如 BK0478=新能源汽车)
            
        Returns:
            StockQuote 或 None
        """
        try:
            url = "http://push2.eastmoney.com/api/qt/stock/get"
            params = {
                "secid": f"90.{sector_code}",
                "fields": "f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f57,f58,f60,f116",
                "ut": "fa5fd1943c7b386f172d6893dbfba10b"
            }
            
            response = self.session.get(url, params=params, timeout=5)
            data = response.json()
            
            if 'data' not in data or data['data'] is None:
                return None
            
            d = data['data']
            
            price = d.get('f43', 0) / 100 if d.get('f43') else 0
            pre_close = d.get('f60', 0) / 100 if d.get('f60') else 0
            change = price - pre_close
            change_pct = (change / pre_close * 100) if pre_close > 0 else 0
            
            market_cap = d.get('f116', 0) / 100000000 if d.get('f116') else 50000
            
            return StockQuote(
                symbol=sector_code,
                name=d.get('f58', ''),
                price=price,
                change=change,
                change_pct=change_pct,
                volume=d.get('f47', 0) / 100 if d.get('f47') else 0,
                amount=d.get('f48', 0) if d.get('f48') else 0,
                market_cap=market_cap,
                float_cap=0,
                pe_ratio=0,
                pb_ratio=0,
                update_time=datetime.now()
            )
            
        except Exception as e:
            print(f"[get_sector_quote] Error: {e}")
            return None
    
    def get_quote(self, symbol: str, entity_type: str = "stock") -> Optional[StockQuote]:
        """
        通用获取行情接口
        
        Args:
            symbol: 代码
            entity_type: 类型 (stock/index/sector)
            
        Returns:
            StockQuote 或 None
        """
        if entity_type == "index":
            return self.get_index_quote(symbol)
        elif entity_type == "sector":
            return self.get_sector_quote(symbol)
        else:
            # 股票优先使用东方财富（有市值数据）
            quote = self.get_quote_eastmoney(symbol)
            if quote is None:
                quote = self.get_quote_sina(symbol)
            return quote
    
    def get_northbound_flow(self) -> Dict:
        """
        获取北向资金流向
        
        Returns:
            北向资金数据
        """
        try:
            url = "http://push2.eastmoney.com/api/qt/kamt.rtmin/get"
            params = {
                "fields1": "f1,f2,f3,f4",
                "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63",
                "ut": "b2884a393a59ad64002292a3e90d46a5"
            }
            
            response = self.session.get(url, params=params, timeout=5)
            data = response.json()
            
            if 'data' not in data:
                return {}
            
            d = data['data']
            
            return {
                "hk_to_sh": d.get('hzTotal', 0) / 10000,  # 沪股通，万元转亿元
                "hk_to_sz": d.get('szTotal', 0) / 10000,  # 深股通
                "total": (d.get('hzTotal', 0) + d.get('szTotal', 0)) / 10000,
                "update_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"[get_northbound_flow] Error: {e}")
            return {}


class HistoricalDataFetcher:
    """
    历史数据获取器
    
    获取K线历史数据用于技术分析
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_kline(self, symbol: str, period: str = "daily", 
                  limit: int = 100) -> Optional[List[Dict]]:
        """
        获取K线数据
        
        Args:
            symbol: 股票代码
            period: 周期 (daily/weekly/monthly)
            limit: 获取条数
            
        Returns:
            K线数据列表
        """
        try:
            # 判断市场
            if symbol.startswith('6'):
                secid = f"1.{symbol}"
            elif symbol.startswith('0') or symbol.startswith('3'):
                secid = f"0.{symbol}"
            else:
                secid = f"1.{symbol}"
            
            # 周期映射
            klt_map = {
                "daily": 101,
                "weekly": 102,
                "monthly": 103
            }
            klt = klt_map.get(period, 101)
            
            url = "http://push2his.eastmoney.com/api/qt/stock/kline/get"
            params = {
                "secid": secid,
                "fields1": "f1,f2,f3,f4,f5,f6",
                "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
                "klt": klt,
                "fqt": 1,  # 前复权
                "end": "20500101",
                "lmt": limit
            }
            
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'data' not in data or data['data'] is None:
                return None
            
            klines = data['data'].get('klines', [])
            result = []
            
            for kline in klines:
                parts = kline.split(',')
                if len(parts) >= 7:
                    result.append({
                        'date': parts[0],
                        'open': float(parts[1]),
                        'close': float(parts[2]),
                        'high': float(parts[3]),
                        'low': float(parts[4]),
                        'volume': float(parts[5]),
                        'amount': float(parts[6])
                    })
            
            return result
            
        except Exception as e:
            print(f"[get_kline] Error: {e}")
            return None


def demo():
    """测试数据获取"""
    print("=" * 60)
    print("实时数据获取测试")
    print("=" * 60)
    
    fetcher = StockDataFetcher()
    
    # 测试股票
    print("\n【个股行情】")
    for symbol in ['600519', '000858', '300750']:
        quote = fetcher.get_quote(symbol, "stock")
        if quote:
            print(f"  {quote.name}({quote.symbol}): "
                  f"价格 {quote.price:.2f}, "
                  f"涨跌 {quote.change_pct:+.2f}%, "
                  f"市值 {quote.market_cap:.0f}亿")
    
    # 测试指数
    print("\n【指数行情】")
    for symbol in ['000001', '399001', '000300']:
        quote = fetcher.get_quote(symbol, "index")
        if quote:
            print(f"  {quote.name}({quote.symbol}): "
                  f"点位 {quote.price:.2f}, "
                  f"涨跌 {quote.change_pct:+.2f}%")
    
    # 测试北向资金
    print("\n【北向资金】")
    flow = fetcher.get_northbound_flow()
    if flow:
        print(f"  沪股通: {flow.get('hk_to_sh', 0):.2f}亿")
        print(f"  深股通: {flow.get('hk_to_sz', 0):.2f}亿")
        print(f"  合计: {flow.get('total', 0):.2f}亿")
    
    # 测试历史数据
    print("\n【历史K线】")
    hist_fetcher = HistoricalDataFetcher()
    klines = hist_fetcher.get_kline('600519', 'daily', 5)
    if klines:
        for k in klines[-3:]:
            print(f"  {k['date']}: 开{k['open']:.2f} 收{k['close']:.2f} "
                  f"量{k['volume']/10000:.0f}万手")


if __name__ == "__main__":
    demo()
