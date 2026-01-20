# -*- coding: utf-8 -*-
"""
A500指数回测脚本
获取过去5天的日涨跌幅数据，与模型预测进行对比
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
from data_fetcher import HistoricalDataFetcher, StockDataFetcher
from datetime import datetime, timedelta
from main import StockForceEngineV2


def get_a500_history():
    """获取A500指数历史数据"""
    print('=' * 60)
    print('获取 563360 A500指数 过去交易日K线数据')
    print('=' * 60)
    
    fetcher = HistoricalDataFetcher()
    
    # 563360 是上海的ETF基金，以5开头
    klines = fetcher.get_kline('563360', 'daily', 15)
    
    if not klines:
        print('获取K线数据失败')
        return None
    
    print(f'\n获取到 {len(klines)} 条K线数据')
    print(f'\n最近交易日涨跌幅：\n')
    print(f"{'日期':<12} {'开盘':<10} {'收盘':<10} {'最高':<10} {'最低':<10} {'涨跌幅':<10}")
    print('-' * 65)
    
    results = []
    prev_close = None
    
    for k in klines:
        change_pct = 0
        if prev_close:
            change_pct = (k['close'] - prev_close) / prev_close * 100
        results.append({
            'date': k['date'],
            'open': k['open'],
            'close': k['close'],
            'high': k['high'],
            'low': k['low'],
            'change_pct': change_pct
        })
        prev_close = k['close']
    
    # 显示最近6天
    for r in results[-6:]:
        print(f"{r['date']:<12} {r['open']:<10.3f} {r['close']:<10.3f} {r['high']:<10.3f} {r['low']:<10.3f} {r['change_pct']:>+6.2f}%")
    
    return results


def get_current_quote():
    """获取当前行情"""
    print('\n【当前实时行情】')
    fetcher = StockDataFetcher()
    quote = fetcher.get_quote('563360', 'stock')
    
    if quote:
        print(f"  代码: {quote.symbol}")
        print(f"  名称: {quote.name}")
        print(f"  价格: {quote.price:.3f}")
        print(f"  涨跌: {quote.change:+.3f} ({quote.change_pct:+.2f}%)")
        return quote
    else:
        print("  获取行情失败")
        return None


def run_model_prediction():
    """运行模型预测"""
    print('\n' + '=' * 60)
    print('力学模型预测')
    print('=' * 60)
    
    api_key = os.environ.get("GEMINI_API_KEY")
    
    engine = StockForceEngineV2(
        use_llm=True,
        llm_api_key=api_key,
        llm_base_url="https://gc.doyo.tv",
        llm_model="gemini-3-pro-preview"
    )
    
    # 添加563360 A500指数
    engine.add_stock('563360', name='A500ETF', entity_type='stock')
    
    # 从数据库获取新闻力量
    engine.add_forces_from_database('563360', hours=48)
    
    # 添加技术面力量
    engine.add_technical_forces('563360')
    
    # 获取分析结果
    result = engine.analyze('563360')
    
    print('\n【模型分析结果】')
    print(f"  净力量: {result['net_force']:.2f}")
    print(f"  加速度: {result['acceleration']:.4f}")
    print(f"  预期日涨跌幅: {result['acceleration']:.2f}%")
    
    # 获取预测
    predictions = result['predictions']
    
    return predictions, result


def run_backtest_comparison():
    """运行回测对比"""
    print('\n' + '=' * 60)
    print('回测分析 - 模型预测 vs 实际涨跌')
    print('=' * 60)
    
    # 获取历史数据
    history = get_a500_history()
    if not history:
        return
    
    quote = get_current_quote()
    
    # 运行模型预测
    predictions, result = run_model_prediction()
    
    # 计算历史统计
    recent_5 = history[-5:]
    avg_change = sum(r['change_pct'] for r in recent_5) / len(recent_5)
    max_change = max(r['change_pct'] for r in recent_5)
    min_change = min(r['change_pct'] for r in recent_5)
    
    print('\n' + '=' * 60)
    print('对比分析')
    print('=' * 60)
    
    print('\n【过去5个交易日实际涨跌】')
    print(f"  平均涨跌幅: {avg_change:+.2f}%")
    print(f"  最大涨幅: {max_change:+.2f}%")
    print(f"  最大跌幅: {min_change:+.2f}%")
    
    # 趋势判断
    up_days = sum(1 for r in recent_5 if r['change_pct'] > 0)
    down_days = sum(1 for r in recent_5 if r['change_pct'] < 0)
    
    print(f"  上涨天数: {up_days}")
    print(f"  下跌天数: {down_days}")
    
    if avg_change > 0.5:
        actual_trend = "强势上涨"
    elif avg_change > 0:
        actual_trend = "温和上涨"
    elif avg_change > -0.5:
        actual_trend = "温和下跌"
    else:
        actual_trend = "强势下跌"
    
    print(f"  实际趋势: {actual_trend}")
    
    print('\n【模型未来5日预测】')
    for p in predictions[:5]:
        print(f"  {p['date']}: {p['trend']} (预期涨跌: {p['expected_change_pct']:+.2f}%)")
    
    # 模型趋势
    model_avg = sum(p['expected_change_pct'] for p in predictions[:5]) / 5
    if model_avg > 0.5:
        model_trend = "强势上涨"
    elif model_avg > 0:
        model_trend = "温和上涨"
    elif model_avg > -0.5:
        model_trend = "温和下跌"
    else:
        model_trend = "强势下跌"
    
    print(f"\n  模型预测平均涨跌: {model_avg:+.2f}%")
    print(f"  模型预测趋势: {model_trend}")
    
    # 一致性分析
    print('\n【一致性分析】')
    
    # 判断方向是否一致
    actual_direction = "涨" if avg_change > 0 else "跌"
    model_direction = "涨" if model_avg > 0 else "跌"
    
    if actual_direction == model_direction:
        print(f"  方向一致性: ✓ 一致 (实际{actual_direction}，模型预测{model_direction})")
    else:
        print(f"  方向一致性: ✗ 不一致 (实际{actual_direction}，模型预测{model_direction})")
    
    # 趋势强度比较
    print(f"  实际趋势: {actual_trend}")
    print(f"  模型趋势: {model_trend}")
    
    if actual_trend == model_trend:
        print(f"  趋势强度: ✓ 完全一致")
    else:
        print(f"  趋势强度: ~ 存在偏差")


def run_historical_backtest(symbol: str = '563360', name: str = 'A500ETF'):
    """
    历史回测：对比过去5天的预期涨跌与实际涨跌
    
    为每一天独立计算技术面力量，模拟真实的日度预测
    
    Args:
        symbol: 股票/ETF代码
        name: 名称
    """
    print('\n' + '=' * 60)
    print(f'历史回测 - {name}({symbol}) 预期涨跌 vs 实际涨跌 (过去5天)')
    print('=' * 60)
    
    # 获取历史数据
    fetcher = HistoricalDataFetcher()
    klines = fetcher.get_kline(symbol, 'daily', 30)  # 获取更多数据用于计算指标
    
    if not klines or len(klines) < 15:
        print('获取历史数据失败')
        return
    
    # 转换为DataFrame
    import pandas as pd
    df = pd.DataFrame(klines)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # 计算每天的实际涨跌幅
    df['change_pct'] = df['close'].pct_change() * 100
    
    print(f"\n获取到 {len(df)} 条历史数据")
    
    # 导入技术面计算器
    from force_indicators import TechnicalForceCalculator
    
    # 取最近6个交易日
    recent_dates = df.index[-6:]
    
    print('\n' + '=' * 60)
    print('逐日回测对比（每日独立计算技术面力量）')
    print('=' * 60)
    
    print(f"\n{'日期':<12} {'实际':<8} {'技术力':<8} {'动量':<8} {'预期':<8} {'偏差':<8} {'方向':<6}")
    print('-' * 70)
    
    backtest_results = []
    
    # 对过去5天进行回测（跳过第一天，因为需要前一天数据）
    for i, test_date in enumerate(recent_dates[1:]):
        # 获取截止到前一天的数据（模拟在当天开盘前预测）
        prev_date = recent_dates[i]
        hist_data = df.loc[:prev_date].copy()
        
        if len(hist_data) < 10:
            continue
        
        # 计算技术面力量
        calculator = TechnicalForceCalculator(hist_data)
        forces = calculator.generate_forces(prev_date.to_pydatetime())
        
        # 计算技术面净力量
        tech_net = sum(
            f.magnitude if f.direction.name == 'BULLISH' else -f.magnitude 
            for f in forces
        )
        
        # 获取所有信号用于分析
        signals = calculator.get_all_signals(prev_date.to_pydatetime())
        
        # 获取市值（动态获取）
        stock_fetcher = StockDataFetcher()
        quote = stock_fetcher.get_quote(symbol, 'stock')
        market_cap = quote.market_cap if quote and quote.market_cap > 0 else 500  # 默认500亿
        
        # 计算前一天的涨跌幅作为动量
        prev_change = df.loc[prev_date, 'change_pct'] if not pd.isna(df.loc[prev_date, 'change_pct']) else 0
        
        # 动量延续因子（前一天涨，今天有延续惯性）
        momentum_factor = prev_change * 0.3
        
        # 计算预期涨跌
        # 技术力贡献 + 动量延续
        tech_contribution = tech_net / (market_cap ** 0.5) * 0.25
        expected_change = tech_contribution + momentum_factor
        
        # 获取实际涨跌
        actual_change = df.loc[test_date, 'change_pct']
        deviation = actual_change - expected_change
        
        # 方向判断
        if (actual_change > 0 and expected_change > 0) or (actual_change < 0 and expected_change < 0):
            direction = "✓"
            direction_correct = True
        elif abs(actual_change) < 0.1 or abs(expected_change) < 0.1:
            direction = "-"
            direction_correct = True
        else:
            direction = "✗"
            direction_correct = False
        
        backtest_results.append({
            'date': test_date.strftime('%Y-%m-%d'),
            'actual': actual_change,
            'tech_force': tech_net,
            'momentum': momentum_factor,
            'expected': expected_change,
            'deviation': deviation,
            'direction_correct': direction_correct,
            'force_count': len(forces),
            'signals': signals
        })
        
        print(f"{test_date.strftime('%Y-%m-%d'):<12} {actual_change:>+6.2f}%  {tech_net:>+6.1f}  {momentum_factor:>+6.2f}%  {expected_change:>+6.2f}%  {deviation:>+6.2f}%  {direction}")
    
    # 显示每天的技术信号详情
    print('\n' + '=' * 60)
    print('技术信号详情')
    print('=' * 60)
    
    for r in backtest_results:
        print(f"\n【{r['date']}】实际: {r['actual']:+.2f}%, 预期: {r['expected']:+.2f}%")
        bullish = [s for s in r['signals'] if s.direction.name == 'BULLISH']
        bearish = [s for s in r['signals'] if s.direction.name == 'BEARISH']
        if bullish:
            print(f"  利多: {', '.join(s.name for s in bullish[:3])}")
        if bearish:
            print(f"  利空: {', '.join(s.name for s in bearish[:3])}")
    
    # 统计分析
    print('\n' + '=' * 60)
    print('回测统计')
    print('=' * 60)
    
    # 方向准确率
    direction_correct_count = sum(1 for r in backtest_results if r['direction_correct'])
    direction_accuracy = direction_correct_count / len(backtest_results) * 100
    
    # 平均偏差
    avg_deviation = sum(abs(r['deviation']) for r in backtest_results) / len(backtest_results)
    
    # 平均实际涨跌
    avg_actual = sum(r['actual'] for r in backtest_results) / len(backtest_results)
    
    # 平均预期涨跌
    avg_expected = sum(r['expected'] for r in backtest_results) / len(backtest_results)
    
    # 相关性（简单计算）
    actual_list = [r['actual'] for r in backtest_results]
    expected_list = [r['expected'] for r in backtest_results]
    
    # 计算相关系数
    n = len(actual_list)
    sum_actual = sum(actual_list)
    sum_expected = sum(expected_list)
    sum_actual_sq = sum(a**2 for a in actual_list)
    sum_expected_sq = sum(e**2 for e in expected_list)
    sum_product = sum(a * e for a, e in zip(actual_list, expected_list))
    
    numerator = n * sum_product - sum_actual * sum_expected
    denominator = ((n * sum_actual_sq - sum_actual**2) * (n * sum_expected_sq - sum_expected**2)) ** 0.5
    
    if denominator != 0:
        correlation = numerator / denominator
    else:
        correlation = 0
    
    print(f"\n【准确性指标】")
    print(f"  方向准确率: {direction_accuracy:.1f}% ({direction_correct_count}/5)")
    print(f"  平均绝对偏差: {avg_deviation:.2f}%")
    print(f"  相关系数: {correlation:.4f}")
    
    print(f"\n【趋势对比】")
    print(f"  实际平均涨跌: {avg_actual:+.2f}%")
    print(f"  预期平均涨跌: {avg_expected:+.2f}%")
    
    # 趋势一致性
    if (avg_actual > 0 and avg_expected > 0) or (avg_actual < 0 and avg_expected < 0):
        print(f"  整体趋势: ✓ 一致")
    else:
        print(f"  整体趋势: ✗ 不一致")
    
    # 评分
    print(f"\n【综合评估】")
    score = 0
    if direction_accuracy >= 80:
        score += 40
        print(f"  方向准确性: 优秀 (+40分)")
    elif direction_accuracy >= 60:
        score += 25
        print(f"  方向准确性: 良好 (+25分)")
    else:
        score += 10
        print(f"  方向准确性: 一般 (+10分)")
    
    if avg_deviation < 0.5:
        score += 30
        print(f"  偏差控制: 优秀 (+30分)")
    elif avg_deviation < 1.0:
        score += 20
        print(f"  偏差控制: 良好 (+20分)")
    else:
        score += 10
        print(f"  偏差控制: 一般 (+10分)")
    
    if correlation > 0.7:
        score += 30
        print(f"  趋势相关性: 优秀 (+30分)")
    elif correlation > 0.3:
        score += 20
        print(f"  趋势相关性: 良好 (+20分)")
    elif correlation > 0:
        score += 10
        print(f"  趋势相关性: 一般 (+10分)")
    else:
        print(f"  趋势相关性: 负相关 (+0分)")
    
    print(f"\n  ★ 回测评分: {score}/100")
    
    if score >= 80:
        print(f"  ★ 模型表现: 优秀")
    elif score >= 60:
        print(f"  ★ 模型表现: 良好")
    elif score >= 40:
        print(f"  ★ 模型表现: 一般")
    else:
        print(f"  ★ 模型表现: 需要优化")


if __name__ == "__main__":
    # 回测恒生科技指数
    run_historical_backtest('513130', '恒生科技指数')
