# -*- coding: utf-8 -*-
"""
股票力学量化模型 - 增强版主入口

整合所有模块，提供完整的分析流程:
- 实时获取股票/指数市值
- 自动获取RSS新闻并使用大模型分析
- 生成力学分析报告
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import numpy as np
import pandas as pd
import json

from stock_force_model import (
    StockEntity, Force, ForceDirection, ForceType,
    StockForceAnalyzer, ForceFactory
)
from force_indicators import (
    TechnicalForceCalculator, FundamentalForceCalculator,
    SentimentForceCalculator
)
from news_parser import NewsForceParser, PolicyForceGenerator, NewsEvent
from backtest import Backtester, ForceBasedStrategy, BacktestResult
from data_fetcher import StockDataFetcher, HistoricalDataFetcher, StockQuote
from rss_analyzer import NewsForceIntegrator, RSSFetcher, ForceAnalysisResult


class StockForceEngineV2:
    """
    股票力学引擎 V2 (增强版)
    
    整合所有模块的主要接口:
    - 实时数据获取
    - 多RSS源新闻分析
    - SQLite数据库持久化
    - 力学模型计算
    """
    
    def __init__(self, 
                 use_llm: bool = False,
                 llm_api_key: str = None,
                 llm_base_url: str = None,
                 llm_model: str = None,
                 config_path: str = None,
                 db_path: str = None):
        """
        初始化引擎
        
        Args:
            use_llm: 是否使用大模型分析新闻
            llm_api_key: Gemini API Key (如果不提供则从配置文件读取)
            llm_base_url: Gemini API URL (如果不提供则从配置文件读取)
            llm_model: 使用的模型 (如果不提供则从配置文件读取)
            config_path: 配置文件路径 (默认config.json)
            db_path: 数据库路径 (如果不提供则从配置文件读取)
        """
        import os
        from rss_database import ConfigManager
        
        # 加载配置文件
        self.config = ConfigManager(config_path or "config.json")
        
        # 如果enable_llm为False，自动从配置文件读取LLM配置
        llm_config = self.config.get_llm_config()
        if not use_llm and llm_config.get('enabled', False):
            use_llm = True
        
        # 如果指定了use_llm=True但未提供API Key，从配置文件读取
        if use_llm and not llm_api_key:
            api_key_str = llm_config.get('api_key', '')
            if api_key_str.startswith('${') and api_key_str.endswith('}'):
                # 环境变量引用格式: ${VARIABLE_NAME}
                env_var = api_key_str[2:-1]
                llm_api_key = os.environ.get(env_var)
            else:
                llm_api_key = api_key_str
        
        # 从配置文件读取其他参数
        if not llm_base_url:
            llm_base_url = llm_config.get('base_url')
        if not llm_model:
            llm_model = llm_config.get('model', 'gemini-3-flash-preview')
        
        # 数据获取器
        self.data_fetcher = StockDataFetcher()
        self.hist_fetcher = HistoricalDataFetcher()
        
        # 新闻分析器（支持多RSS源和数据库）
        self.news_integrator = NewsForceIntegrator(
            use_llm=use_llm,
            api_key=llm_api_key,
            base_url=llm_base_url,
            model=llm_model,
            config_path=config_path,
            db_path=db_path or self.config.get_database_config().get('path', 'rss_news.db')
        )
        
        # 传统新闻解析器
        self.news_parser = NewsForceParser()
        
        # 股票实体和分析器
        self.stocks: Dict[str, StockEntity] = {}
        self.analyzers: Dict[str, StockForceAnalyzer] = {}
        self.quotes: Dict[str, StockQuote] = {}
    
    def add_stock(self, symbol: str, name: str = None, 
                 entity_type: str = "stock",
                 fetch_realtime: bool = True) -> StockEntity:
        """
        添加股票实体，自动获取实时市值
        
        Args:
            symbol: 股票代码
            name: 名称（如果不传则自动获取）
            entity_type: 实体类型 (stock/index/sector)
            fetch_realtime: 是否获取实时数据
            
        Returns:
            股票实体
        """
        market_cap = 0
        stock_name = name or symbol
        
        # 获取实时数据
        if fetch_realtime:
            print(f"[Engine] 获取 {symbol} 实时数据...")
            quote = self.data_fetcher.get_quote(symbol, entity_type)
            
            if quote:
                self.quotes[symbol] = quote
                stock_name = quote.name or name or symbol
                market_cap = quote.market_cap
                print(f"  [+] {stock_name}: 价格 {quote.price:.2f}, "
                      f"涨跌 {quote.change_pct:+.2f}%, 市值 {market_cap:.0f}亿")
            else:
                print(f"  [-] 获取失败，使用默认值")
                market_cap = self._get_default_market_cap(entity_type)
        else:
            market_cap = self._get_default_market_cap(entity_type)
        
        # 创建实体
        stock = StockEntity(
            symbol=symbol,
            name=stock_name,
            market_cap=market_cap,
            entity_type=entity_type
        )
        
        self.stocks[symbol] = stock
        self.analyzers[symbol] = StockForceAnalyzer(stock)
        
        return stock
    
    def _get_default_market_cap(self, entity_type: str) -> float:
        """获取默认市值"""
        defaults = {
            "stock": 1000,
            "index": 500000,
            "sector": 50000
        }
        return defaults.get(entity_type, 1000)
    
    def refresh_quote(self, symbol: str) -> Optional[StockQuote]:
        """
        刷新股票行情
        
        Args:
            symbol: 股票代码
            
        Returns:
            最新行情
        """
        if symbol not in self.stocks:
            return None
        
        stock = self.stocks[symbol]
        quote = self.data_fetcher.get_quote(symbol, stock.entity_type)
        
        if quote:
            self.quotes[symbol] = quote
            # 更新市值
            if quote.market_cap > 0:
                stock.market_cap = quote.market_cap
        
        return quote
    
    def add_force_to_stock(self, symbol: str, force: Force):
        """
        为股票添加力
        
        Args:
            symbol: 股票代码
            force: 力对象
        """
        if symbol in self.stocks:
            self.stocks[symbol].add_force(force)
    
    def fetch_and_add_rss_forces(self, symbol: str = None, 
                                  max_items: int = 20) -> List[Tuple[str, Force]]:
        """
        获取RSS新闻并添加为力
        
        Args:
            symbol: 目标股票代码（如果为None则只返回不添加）
            max_items: 最大获取条数
            
        Returns:
            (股票代码, Force) 列表
        """
        print("\n[Engine] 获取并分析RSS新闻...")
        
        results = self.news_integrator.fetch_and_analyze_cls(max_items=max_items)
        
        if not results:
            print("[Engine] 没有可用的新闻力量")
            return []
        
        added_forces = []
        
        for news, analysis in results:
            # 创建Force对象
            direction_map = {
                "bullish": ForceDirection.BULLISH,
                "bearish": ForceDirection.BEARISH,
                "neutral": ForceDirection.NEUTRAL
            }
            
            type_map = {
                "long_term": ForceType.LONG_TERM,
                "mid_term": ForceType.MID_TERM,
                "short_term": ForceType.SHORT_TERM
            }
            
            decay_rates = {
                "long_term": 0.001,
                "mid_term": 0.01,
                "short_term": 0.1
            }
            
            force = Force(
                name=f"[RSS] {news.title[:35]}",
                magnitude=analysis.magnitude,
                direction=direction_map.get(analysis.direction, ForceDirection.NEUTRAL),
                force_type=type_map.get(analysis.force_type, ForceType.SHORT_TERM),
                start_date=news.pub_date,
                decay_rate=decay_rates.get(analysis.force_type, 0.1),
                confidence=analysis.confidence,
                source=f"rss:cls"
            )
            
            # 如果指定了symbol，添加到该股票
            if symbol and symbol in self.stocks:
                self.add_force_to_stock(symbol, force)
                added_forces.append((symbol, force))
            
            # 如果分析结果指定了受影响的股票，也添加
            for affected_symbol in analysis.affected_symbols:
                if affected_symbol in self.stocks:
                    # 复制一个新的Force对象
                    new_force = Force(
                        name=force.name,
                        magnitude=force.magnitude,
                        direction=force.direction,
                        force_type=force.force_type,
                        start_date=force.start_date,
                        decay_rate=force.decay_rate,
                        confidence=force.confidence,
                        source=force.source
                    )
                    self.add_force_to_stock(affected_symbol, new_force)
                    added_forces.append((affected_symbol, new_force))
        
        print(f"[Engine] 共添加 {len(added_forces)} 个RSS新闻力量")
        return added_forces
    
    def run_incremental_rss_analysis(self) -> Dict:
        """
        运行增量RSS分析
        
        从所有配置的RSS源获取新闻，只分析新增的新闻
        
        Returns:
            运行统计信息
        """
        print("\n[Engine] 运行增量RSS分析...")
        return self.news_integrator.run_incremental_analysis()
    
    def add_forces_from_database(self, symbol: str, hours: int = 24) -> List[Tuple[str, Force]]:
        """
        从数据库获取最近的力量新闻并添加到股票
        
        Args:
            symbol: 股票代码
            hours: 获取最近多少小时的新闻
            
        Returns:
            添加的 (symbol, Force) 列表
        """
        if symbol not in self.stocks:
            print(f"[Engine] 股票 {symbol} 未添加")
            return []
        
        print(f"[Engine] 从数据库获取最近{hours}小时的力量新闻...")
        
        results = self.news_integrator.get_recent_forces(hours=hours)
        
        if not results:
            print("[Engine] 数据库中没有可用的力量新闻")
            return []
        
        direction_map = {
            "bullish": ForceDirection.BULLISH,
            "bearish": ForceDirection.BEARISH,
            "neutral": ForceDirection.NEUTRAL
        }
        
        type_map = {
            "long_term": ForceType.LONG_TERM,
            "mid_term": ForceType.MID_TERM,
            "short_term": ForceType.SHORT_TERM
        }
        
        decay_rates = {
            "long_term": 0.001,
            "mid_term": 0.01,
            "short_term": 0.1
        }
        
        added_forces = []
        
        for news, analysis in results:
            force = Force(
                name=f"[DB] {news.title[:35]}",
                magnitude=analysis.magnitude,
                direction=direction_map.get(analysis.direction, ForceDirection.NEUTRAL),
                force_type=type_map.get(analysis.force_type, ForceType.SHORT_TERM),
                start_date=news.pub_date,
                decay_rate=decay_rates.get(analysis.force_type, 0.1),
                confidence=analysis.confidence,
                source=f"db:{news.source}"
            )
            
            self.add_force_to_stock(symbol, force)
            added_forces.append((symbol, force))
        
        print(f"[Engine] 从数据库添加 {len(added_forces)} 个力量")
        return added_forces
    
    def get_rss_statistics(self) -> Dict:
        """获取RSS数据库统计信息"""
        return self.news_integrator.get_statistics()
    
    def show_configured_sources(self):
        """显示配置的RSS源"""
        sources = self.news_integrator.config.get_enabled_sources()
        print("\n【配置的RSS源】")
        for s in sources:
            print(f"  - {s['name']}: {s['url']}")
        return sources
    
    def add_technical_forces(self, symbol: str, 
                            date: datetime = None,
                            days: int = 100) -> List[Force]:
        """
        添加技术面力量（自动获取历史数据）
        
        Args:
            symbol: 股票代码
            date: 分析日期
            days: 获取的历史天数
            
        Returns:
            添加的Force列表
        """
        if symbol not in self.stocks:
            return []
        
        if date is None:
            date = datetime.now()
        
        print(f"[Engine] 获取 {symbol} 历史K线数据...")
        
        # 获取历史数据
        klines = self.hist_fetcher.get_kline(symbol, 'daily', days)
        
        if not klines:
            print(f"  [-] 获取历史数据失败")
            return []
        
        # 转换为DataFrame
        df = pd.DataFrame(klines)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df = df.rename(columns={
            'open': 'open',
            'close': 'close', 
            'high': 'high',
            'low': 'low',
            'volume': 'volume'
        })
        
        print(f"  [+] 获取到 {len(df)} 条K线数据")
        
        # 计算技术指标并生成力
        calculator = TechnicalForceCalculator(df)
        
        # 找到最接近date的交易日
        target_date = pd.Timestamp(date)
        if target_date in df.index:
            analysis_date = target_date
        else:
            # 找最近的日期
            dates_before = df.index[df.index <= target_date]
            if len(dates_before) > 0:
                analysis_date = dates_before[-1]
            else:
                analysis_date = df.index[-1]
        
        forces = calculator.generate_forces(analysis_date.to_pydatetime())
        
        for force in forces:
            self.add_force_to_stock(symbol, force)
        
        print(f"  [+] 生成 {len(forces)} 个技术面力量")
        return forces
    
    def add_northbound_force(self, date: datetime = None) -> Optional[Force]:
        """
        添加北向资金力量
        
        Args:
            date: 日期
            
        Returns:
            Force对象或None
        """
        if date is None:
            date = datetime.now()
        
        print("[Engine] 获取北向资金数据...")
        
        flow = self.data_fetcher.get_northbound_flow()
        
        if not flow:
            print("  [-] 获取失败")
            return None
        
        total = flow.get('total', 0)
        
        if abs(total) < 10:  # 小于10亿忽略
            print(f"  → 北向资金 {total:.2f}亿，影响较小")
            return None
        
        # 创建力
        if total > 0:
            direction = ForceDirection.BULLISH
            name = f"北向资金净流入{total:.0f}亿"
        else:
            direction = ForceDirection.BEARISH
            name = f"北向资金净流出{abs(total):.0f}亿"
        
        magnitude = min(abs(total) / 5, 50)  # 最大50
        
        force = Force(
            name=name,
            magnitude=magnitude,
            direction=direction,
            force_type=ForceType.SHORT_TERM,
            start_date=date,
            decay_rate=0.1,
            confidence=0.75,
            source="northbound"
        )
        
        print(f"  [+] {name} (力度: {magnitude:.1f})")
        
        return force
    
    def analyze(self, symbol: str, date: datetime = None) -> Dict:
        """
        分析股票
        
        Args:
            symbol: 股票代码
            date: 分析日期
            
        Returns:
            分析结果字典
        """
        if symbol not in self.analyzers:
            raise ValueError(f"Stock {symbol} not found")
        
        if date is None:
            date = datetime.now()
        
        analyzer = self.analyzers[symbol]
        stock = self.stocks[symbol]
        
        # 清理过期的力
        stock.remove_inactive_forces(date)
        
        # 获取最新行情
        quote = self.quotes.get(symbol)
        
        result = {
            "symbol": symbol,
            "name": stock.name,
            "date": date.strftime("%Y-%m-%d %H:%M"),
            "market_cap": stock.market_cap,
            "net_force": analyzer.calculate_net_force(date),
            "acceleration": analyzer.calculate_acceleration(date),
            "force_by_type": {
                k.value: v for k, v in 
                analyzer.calculate_force_by_type(date).items()
            },
            "decomposition": analyzer.get_force_decomposition(date),
            "predictions": analyzer.predict_trend(date, days=5),
            "force_count": len(stock.forces)
        }
        
        # 添加实时行情信息
        if quote:
            result["quote"] = {
                "price": quote.price,
                "change": quote.change,
                "change_pct": quote.change_pct,
                "volume": quote.volume,
                "pe_ratio": quote.pe_ratio
            }
        
        return result
    
    def get_report(self, symbol: str, date: datetime = None) -> str:
        """
        获取分析报告
        
        Args:
            symbol: 股票代码
            date: 分析日期
            
        Returns:
            报告文本
        """
        if symbol not in self.analyzers:
            raise ValueError(f"Stock {symbol} not found")
        
        if date is None:
            date = datetime.now()
        
        # 获取行情信息
        quote = self.quotes.get(symbol)
        quote_info = ""
        if quote:
            quote_info = f"""
【实时行情】
当前价格: {quote.price:.2f}
今日涨跌: {quote.change:+.2f} ({quote.change_pct:+.2f}%)
成交量: {quote.volume/10000:.2f}万手
成交额: {quote.amount/100000000:.2f}亿
市盈率: {quote.pe_ratio:.2f}
市净率: {quote.pb_ratio:.2f}
"""
        
        # 生成基础报告
        base_report = self.analyzers[symbol].generate_report(date)
        
        # 插入行情信息
        if quote_info:
            lines = base_report.split('\n')
            insert_idx = 0
            for i, line in enumerate(lines):
                if '【基本信息】' in line:
                    insert_idx = i + 6  # 在基本信息后插入
                    break
            lines.insert(insert_idx, quote_info)
            base_report = '\n'.join(lines)
        
        return base_report
    
    def run_full_analysis(self, symbol: str, 
                         entity_type: str = "stock",
                         include_rss: bool = True,
                         include_technical: bool = True,
                         include_northbound: bool = True) -> str:
        """
        运行完整分析流程
        
        Args:
            symbol: 股票代码
            entity_type: 实体类型
            include_rss: 是否包含RSS新闻分析
            include_technical: 是否包含技术面分析
            include_northbound: 是否包含北向资金
            
        Returns:
            完整分析报告
        """
        current_date = datetime.now()
        
        print(f"\n{'='*60}")
        print(f"开始完整分析: {symbol}")
        print(f"{'='*60}")
        
        # 1. 添加股票并获取实时数据
        stock = self.add_stock(symbol, entity_type=entity_type, fetch_realtime=True)
        
        # 2. 添加技术面力量
        if include_technical:
            self.add_technical_forces(symbol, current_date)
        
        # 3. 添加北向资金力量
        if include_northbound and entity_type in ["stock", "index"]:
            nb_force = self.add_northbound_force(current_date)
            if nb_force:
                self.add_force_to_stock(symbol, nb_force)
        
        # 4. 获取并分析RSS新闻
        if include_rss:
            self.fetch_and_add_rss_forces(symbol, max_items=15)
        
        # 5. 生成报告
        report = self.get_report(symbol, current_date)
        
        return report


def _print_prediction_summary(all_analysis: List[Dict]):
    """
    打印多股票预测汇总对比表
    
    Args:
        all_analysis: 所有股票的分析结果列表
    """
    if not all_analysis:
        return
    
    print("\n" + "=" * 100)
    print("【多股票预测汇总对比】")
    print("=" * 100)
    
    # 1. 当前状态对比表
    print("\n[当前力学状态对比]")
    print("-" * 100)
    header = f"{'股票':<15} {'代码':<10} {'合力':<10} {'加速度':<10} {'多空比':<10} {'力量数':<8} {'趋势判断':<12}"
    print(header)
    print("-" * 100)
    
    for analysis in all_analysis:
        symbol = analysis['symbol']
        name = analysis['name'][:6] if len(analysis['name']) > 6 else analysis['name']
        net_force = analysis['net_force']
        acceleration = analysis['acceleration']
        decomp = analysis['decomposition']
        force_ratio = decomp.get('force_ratio', 0)
        force_count = analysis['force_count']
        
        # 判断趋势
        if acceleration > 0.5:
            trend = "强势看涨"
        elif acceleration > 0.1:
            trend = "温和看涨"
        elif acceleration > -0.1:
            trend = "横盘震荡"
        elif acceleration > -0.5:
            trend = "温和看跌"
        else:
            trend = "强势看跌"
        
        # 格式化多空比
        if force_ratio == float('inf'):
            ratio_str = "全多"
        elif force_ratio == 0:
            ratio_str = "全空"
        else:
            ratio_str = f"{force_ratio:.2f}"
        
        row = f"{name:<15} {symbol:<10} {net_force:>8.2f} {acceleration:>9.4f} {ratio_str:>9} {force_count:>7} {trend:<12}"
        print(row)
    
    print("-" * 100)
    
    # 2. 分类力量对比
    print("\n[分类力量对比]")
    print("-" * 80)
    header2 = f"{'股票':<15} {'长期力':<12} {'中期力':<12} {'短期力':<12} {'主导力量':<15}"
    print(header2)
    print("-" * 80)
    
    for analysis in all_analysis:
        name = analysis['name'][:6] if len(analysis['name']) > 6 else analysis['name']
        force_by_type = analysis['force_by_type']
        
        long_term = force_by_type.get('long_term', 0)
        mid_term = force_by_type.get('mid_term', 0)
        short_term = force_by_type.get('short_term', 0)
        
        # 判断主导力量
        forces = {'长期': abs(long_term), '中期': abs(mid_term), '短期': abs(short_term)}
        dominant = max(forces, key=forces.get)
        dominant_value = forces[dominant]
        
        row = f"{name:<15} {long_term:>10.2f} {mid_term:>10.2f} {short_term:>10.2f} {dominant}({dominant_value:.1f})"
        print(row)
    
    print("-" * 80)
    
    # 3. 未来5日预测对比
    print("\n[未来5日趋势预测对比]")
    print("-" * 100)
    
    # 获取预测日期
    if all_analysis and all_analysis[0].get('predictions'):
        dates = [p['date'] for p in all_analysis[0]['predictions']]
        date_header = "  ".join([d[5:] for d in dates])  # 只显示月-日
        header3 = f"{'股票':<15} {date_header}"
        print(header3)
        print("-" * 100)
        
        for analysis in all_analysis:
            name = analysis['name'][:6] if len(analysis['name']) > 6 else analysis['name']
            predictions = analysis.get('predictions', [])
            
            if predictions:
                # 显示预期涨跌幅
                pred_values = []
                for pred in predictions:
                    change = pred['expected_change_pct']
                    if change > 0:
                        pred_values.append(f"+{change:.2f}%")
                    else:
                        pred_values.append(f"{change:.2f}%")
                
                pred_str = "  ".join([f"{v:>7}" for v in pred_values])
                print(f"{name:<15} {pred_str}")
        
        print("-" * 100)
    
    # 4. 综合评分排名
    print("\n[综合评分排名]")
    print("-" * 60)
    
    # 计算综合评分
    scored_stocks = []
    for analysis in all_analysis:
        symbol = analysis['symbol']
        name = analysis['name']
        
        # 综合评分 = 加速度 * 100 + 多空比权重
        acceleration = analysis['acceleration']
        decomp = analysis['decomposition']
        force_ratio = decomp.get('force_ratio', 1)
        if force_ratio == float('inf'):
            force_ratio = 10
        
        # 评分公式
        score = acceleration * 50 + min(force_ratio, 10) * 5
        
        # 趋势判断
        if acceleration > 0.5:
            trend = "强势看涨 [+++]"
            recommendation = "积极关注"
        elif acceleration > 0.1:
            trend = "温和看涨 [++]"
            recommendation = "适度关注"
        elif acceleration > -0.1:
            trend = "横盘震荡 [~]"
            recommendation = "观望为主"
        elif acceleration > -0.5:
            trend = "温和看跌 [--]"
            recommendation = "谨慎操作"
        else:
            trend = "强势看跌 [---]"
            recommendation = "规避风险"
        
        scored_stocks.append({
            'symbol': symbol,
            'name': name,
            'score': score,
            'trend': trend,
            'recommendation': recommendation
        })
    
    # 按评分排序
    scored_stocks.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"{'排名':<6} {'股票':<15} {'评分':<10} {'趋势':<18} {'建议':<12}")
    print("-" * 60)
    
    for i, stock in enumerate(scored_stocks, 1):
        name = stock['name'][:6] if len(stock['name']) > 6 else stock['name']
        print(f"{i:<6} {name:<15} {stock['score']:>8.2f} {stock['trend']:<18} {stock['recommendation']:<12}")
    
    print("-" * 60)
    
    # 5. 总结
    print("\n[分析总结]")
    print("-" * 60)
    
    bullish_count = sum(1 for a in all_analysis if a['acceleration'] > 0.1)
    bearish_count = sum(1 for a in all_analysis if a['acceleration'] < -0.1)
    neutral_count = len(all_analysis) - bullish_count - bearish_count
    
    print(f"分析股票总数: {len(all_analysis)}")
    print(f"  - 看涨: {bullish_count} 只")
    print(f"  - 看跌: {bearish_count} 只")
    print(f"  - 震荡: {neutral_count} 只")
    
    if scored_stocks:
        best = scored_stocks[0]
        worst = scored_stocks[-1]
        print(f"\n最强势股票: {best['name']} (评分: {best['score']:.2f})")
        print(f"最弱势股票: {worst['name']} (评分: {worst['score']:.2f})")
    
    print("\n" + "=" * 100)
    print("注意: 以上分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。")
    print("=" * 100)


def demo_with_llm():
    """
    使用大模型的分析演示
    
    从config.json读取大模型配置
    """
    import os
    
    # 创建引擎（配置文件路径默认为config.json）
    engine = StockForceEngineV2(
        use_llm=True,
        config_path="config.json"
    )
    
    # 从配置文件读取LLM配置
    llm_config = engine.news_integrator.config.get_llm_config()
    
    if not llm_config.get('enabled', False):
        print("[Engine] 大模型未启用，请在config.json中设置 llm.enabled=true")
        return
    
    # 获取API Key（支持环境变量引用，如 ${GEMINI_API_KEY}）
    api_key = llm_config.get('api_key', '')
    if api_key.startswith('${') and api_key.endswith('}'):
        env_var = api_key[2:-1]
        api_key = os.environ.get(env_var, '')
        if not api_key:
            print(f"[Engine] 未设置环境变量: {env_var}")
            return
    
    print(f"\n[Config] 大模型配置:")
    print(f"  - 提供商: {llm_config.get('provider', 'unknown')}")
    print(f"  - 模型: {llm_config.get('model', 'unknown')}")
    print(f"  - API Base: {llm_config.get('base_url', 'default')}")
    
    # 显示配置的RSS源
    engine.show_configured_sources()
    
    # 从配置文件获取启用的股票
    stocks = engine.news_integrator.config.get_enabled_stocks()
    
    if not stocks:
        print("[Engine] 配置文件中没有启用的股票，使用默认股票 600519")
        stocks = [{"symbol": "600519", "name": "贵州茅台", "entity_type": "stock"}]
    
    print(f"\n【配置的股票】")
    for s in stocks:
        print(f"  - {s['symbol']} {s.get('name', '')}")
    
    # 运行增量RSS分析
    print("\n" + "=" * 60)
    engine.run_incremental_rss_analysis()
    
    # 收集所有股票的分析报告和分析数据
    all_reports = []
    all_analysis = []
    current_date = datetime.now()
    
    # 分析所有启用的股票
    for stock_config in stocks:
        symbol = stock_config['symbol']
        entity_type = stock_config.get('entity_type', 'stock')
        
        print(f"\n分析股票: {symbol} {stock_config.get('name', '')}")
        
        # 添加股票
        engine.add_stock(symbol, name=stock_config.get('name'), entity_type=entity_type)
        
        # 从数据库获取力量
        engine.add_forces_from_database(symbol, hours=24)
        
        # 添加技术面力量
        engine.add_technical_forces(symbol)
        
        # 获取分析数据
        analysis = engine.analyze(symbol, current_date)
        all_analysis.append(analysis)
        
        # 生成报告
        report = engine.get_report(symbol, current_date)
        all_reports.append((symbol, stock_config.get('name', ''), report))
    
    # 一次性输出所有报告
    print("\n" + "=" * 80)
    print("【最终分析报告汇总】")
    print("=" * 80)
    
    for symbol, name, report in all_reports:
        print(report)
        print("\n" + "-" * 80 + "\n")
    
    # 输出多股票预测对比汇总
    _print_prediction_summary(all_analysis)

if __name__ == "__main__":
    demo_with_llm()
