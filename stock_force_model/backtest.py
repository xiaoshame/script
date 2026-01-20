# -*- coding: utf-8 -*-
"""
回测框架模块

用于验证股票力学模型的历史表现
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

from stock_force_model import (
    StockEntity, Force, ForceDirection, ForceType,
    StockForceAnalyzer, ForceFactory
)
from force_indicators import TechnicalForceCalculator


class SignalType(Enum):
    """信号类型"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class TradeSignal:
    """交易信号"""
    date: datetime
    signal_type: SignalType
    strength: float  # 信号强度 0-100
    reason: str
    acceleration: float
    net_force: float


@dataclass
class Trade:
    """交易记录"""
    entry_date: datetime
    exit_date: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    shares: int
    direction: str  # 'long' or 'short'
    entry_reason: str
    exit_reason: str = ""
    profit_loss: float = 0.0
    profit_loss_pct: float = 0.0
    holding_days: int = 0


@dataclass
class BacktestResult:
    """回测结果"""
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_pct: float
    annualized_return: float
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_profit_per_trade: float
    avg_holding_days: float
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[Dict] = field(default_factory=list)


class ForceBasedStrategy:
    """
    基于力学模型的交易策略
    
    根据合力和加速度生成买卖信号
    """
    
    def __init__(self,
                 acceleration_buy_threshold: float = 0.3,
                 acceleration_sell_threshold: float = -0.3,
                 force_ratio_buy_threshold: float = 1.5,
                 force_ratio_sell_threshold: float = 0.67,
                 min_holding_days: int = 3,
                 max_holding_days: int = 30,
                 stop_loss_pct: float = 0.08,
                 take_profit_pct: float = 0.15):
        """
        初始化策略参数
        
        Args:
            acceleration_buy_threshold: 买入加速度阈值
            acceleration_sell_threshold: 卖出加速度阈值
            force_ratio_buy_threshold: 买入多空力量比阈值
            force_ratio_sell_threshold: 卖出多空力量比阈值
            min_holding_days: 最小持仓天数
            max_holding_days: 最大持仓天数
            stop_loss_pct: 止损比例
            take_profit_pct: 止盈比例
        """
        self.acceleration_buy_threshold = acceleration_buy_threshold
        self.acceleration_sell_threshold = acceleration_sell_threshold
        self.force_ratio_buy_threshold = force_ratio_buy_threshold
        self.force_ratio_sell_threshold = force_ratio_sell_threshold
        self.min_holding_days = min_holding_days
        self.max_holding_days = max_holding_days
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
    
    def generate_signal(self, analyzer: StockForceAnalyzer,
                       date: datetime,
                       current_position: Optional[Trade] = None) -> TradeSignal:
        """
        生成交易信号
        
        Args:
            analyzer: 力学分析器
            date: 当前日期
            current_position: 当前持仓
            
        Returns:
            交易信号
        """
        acceleration = analyzer.calculate_acceleration(date)
        net_force = analyzer.calculate_net_force(date)
        decomposition = analyzer.get_force_decomposition(date)
        force_ratio = decomposition['force_ratio']
        
        # 如果有持仓，检查是否需要平仓
        if current_position is not None:
            # 检查是否达到最大持仓天数
            holding_days = (date - current_position.entry_date).days
            
            if holding_days >= self.max_holding_days:
                return TradeSignal(
                    date=date,
                    signal_type=SignalType.SELL,
                    strength=80,
                    reason="达到最大持仓天数",
                    acceleration=acceleration,
                    net_force=net_force
                )
            
            # 检查是否满足卖出条件（力量反转）
            if (holding_days >= self.min_holding_days and
                acceleration < self.acceleration_sell_threshold and
                force_ratio < self.force_ratio_sell_threshold):
                return TradeSignal(
                    date=date,
                    signal_type=SignalType.SELL,
                    strength=abs(acceleration) * 100,
                    reason=f"力量反转(加速度:{acceleration:.2f}, 多空比:{force_ratio:.2f})",
                    acceleration=acceleration,
                    net_force=net_force
                )
            
            return TradeSignal(
                date=date,
                signal_type=SignalType.HOLD,
                strength=0,
                reason="继续持有",
                acceleration=acceleration,
                net_force=net_force
            )
        
        # 没有持仓，检查是否满足买入条件
        if (acceleration > self.acceleration_buy_threshold and
            force_ratio > self.force_ratio_buy_threshold):
            
            # 计算信号强度
            strength = min(
                (acceleration * 50 + (force_ratio - 1) * 30),
                100
            )
            
            return TradeSignal(
                date=date,
                signal_type=SignalType.BUY,
                strength=strength,
                reason=f"力量向上(加速度:{acceleration:.2f}, 多空比:{force_ratio:.2f})",
                acceleration=acceleration,
                net_force=net_force
            )
        
        return TradeSignal(
            date=date,
            signal_type=SignalType.HOLD,
            strength=0,
            reason="无信号",
            acceleration=acceleration,
            net_force=net_force
        )


class Backtester:
    """
    回测引擎
    
    使用历史数据验证策略表现
    """
    
    def __init__(self,
                 prices: pd.DataFrame,
                 stock: StockEntity,
                 strategy: ForceBasedStrategy,
                 initial_capital: float = 100000):
        """
        初始化回测引擎
        
        Args:
            prices: 价格数据 (需要包含 'open', 'high', 'low', 'close', 'volume')
            stock: 股票实体
            strategy: 交易策略
            initial_capital: 初始资金
        """
        self.prices = prices.copy()
        self.stock = stock
        self.strategy = strategy
        self.initial_capital = initial_capital
        
        # 初始化技术指标计算器
        self.tech_calculator = TechnicalForceCalculator(prices)
    
    def run(self, start_date: datetime, end_date: datetime,
           external_forces: List[Force] = None) -> BacktestResult:
        """
        运行回测
        
        Args:
            start_date: 回测开始日期
            end_date: 回测结束日期
            external_forces: 外部力（如政策、新闻等）
            
        Returns:
            回测结果
        """
        # 初始化
        capital = self.initial_capital
        position = None
        trades = []
        equity_curve = []
        
        # 添加外部力到股票实体
        if external_forces:
            for force in external_forces:
                self.stock.add_force(force)
        
        # 获取回测日期范围内的交易日
        trading_dates = self.prices.loc[start_date:end_date].index
        
        for date in trading_dates:
            date = pd.Timestamp(date).to_pydatetime()
            
            # 清理过期的力
            self.stock.remove_inactive_forces(date)
            
            # 添加当天的技术面力量
            tech_forces = self.tech_calculator.generate_forces(date)
            for force in tech_forces:
                self.stock.add_force(force)
            
            # 创建分析器
            analyzer = StockForceAnalyzer(self.stock)
            
            # 生成信号
            signal = self.strategy.generate_signal(analyzer, date, position)
            
            # 获取当天价格
            try:
                day_data = self.prices.loc[date]
                close_price = day_data['close']
            except KeyError:
                continue
            
            # 计算当前权益
            if position is not None:
                position_value = position.shares * close_price
                current_equity = capital + position_value
                
                # 检查止损止盈
                profit_pct = (close_price - position.entry_price) / position.entry_price
                
                if profit_pct <= -self.strategy.stop_loss_pct:
                    # 触发止损
                    signal = TradeSignal(
                        date=date,
                        signal_type=SignalType.SELL,
                        strength=100,
                        reason=f"触发止损({profit_pct*100:.1f}%)",
                        acceleration=signal.acceleration,
                        net_force=signal.net_force
                    )
                elif profit_pct >= self.strategy.take_profit_pct:
                    # 触发止盈
                    signal = TradeSignal(
                        date=date,
                        signal_type=SignalType.SELL,
                        strength=100,
                        reason=f"触发止盈({profit_pct*100:.1f}%)",
                        acceleration=signal.acceleration,
                        net_force=signal.net_force
                    )
            else:
                current_equity = capital
            
            # 执行交易
            if signal.signal_type == SignalType.BUY and position is None:
                # 买入
                shares = int(capital * 0.95 / close_price)  # 使用95%资金
                if shares > 0:
                    cost = shares * close_price
                    capital -= cost
                    position = Trade(
                        entry_date=date,
                        exit_date=None,
                        entry_price=close_price,
                        exit_price=None,
                        shares=shares,
                        direction='long',
                        entry_reason=signal.reason
                    )
            
            elif signal.signal_type == SignalType.SELL and position is not None:
                # 卖出
                revenue = position.shares * close_price
                capital += revenue
                
                position.exit_date = date
                position.exit_price = close_price
                position.exit_reason = signal.reason
                position.profit_loss = revenue - (position.shares * position.entry_price)
                position.profit_loss_pct = (close_price - position.entry_price) / position.entry_price
                position.holding_days = (date - position.entry_date).days
                
                trades.append(position)
                position = None
            
            # 记录权益曲线
            if position is not None:
                equity = capital + position.shares * close_price
            else:
                equity = capital
            
            equity_curve.append({
                'date': date.strftime('%Y-%m-%d'),
                'equity': equity,
                'capital': capital,
                'position_value': equity - capital,
                'acceleration': signal.acceleration,
                'net_force': signal.net_force,
                'signal': signal.signal_type.value
            })
        
        # 如果回测结束时还有持仓，强制平仓
        if position is not None:
            last_price = self.prices.iloc[-1]['close']
            revenue = position.shares * last_price
            capital += revenue
            
            position.exit_date = trading_dates[-1].to_pydatetime()
            position.exit_price = last_price
            position.exit_reason = "回测结束强制平仓"
            position.profit_loss = revenue - (position.shares * position.entry_price)
            position.profit_loss_pct = (last_price - position.entry_price) / position.entry_price
            position.holding_days = (position.exit_date - position.entry_date).days
            trades.append(position)
        
        # 计算回测指标
        result = self._calculate_metrics(
            start_date, end_date, capital, trades, equity_curve
        )
        
        return result
    
    def _calculate_metrics(self, start_date: datetime, end_date: datetime,
                          final_capital: float, trades: List[Trade],
                          equity_curve: List[Dict]) -> BacktestResult:
        """
        计算回测指标
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            final_capital: 最终资金
            trades: 交易记录
            equity_curve: 权益曲线
            
        Returns:
            回测结果
        """
        # 基本收益指标
        total_return = final_capital - self.initial_capital
        total_return_pct = total_return / self.initial_capital
        
        # 年化收益
        days = (end_date - start_date).days
        if days > 0:
            annualized_return = (1 + total_return_pct) ** (365 / days) - 1
        else:
            annualized_return = 0
        
        # 最大回撤
        if equity_curve:
            equities = [e['equity'] for e in equity_curve]
            max_equity = equities[0]
            max_drawdown = 0
            max_drawdown_pct = 0
            
            for equity in equities:
                if equity > max_equity:
                    max_equity = equity
                drawdown = max_equity - equity
                drawdown_pct = drawdown / max_equity
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                    max_drawdown_pct = drawdown_pct
        else:
            max_drawdown = 0
            max_drawdown_pct = 0
        
        # 交易统计
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.profit_loss > 0])
        losing_trades = len([t for t in trades if t.profit_loss <= 0])
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # 盈亏比
        total_profit = sum(t.profit_loss for t in trades if t.profit_loss > 0)
        total_loss = abs(sum(t.profit_loss for t in trades if t.profit_loss < 0))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # 平均每笔收益
        avg_profit_per_trade = total_return / total_trades if total_trades > 0 else 0
        
        # 平均持仓天数
        avg_holding_days = np.mean([t.holding_days for t in trades]) if trades else 0
        
        # 夏普比率 (简化计算)
        if equity_curve and len(equity_curve) > 1:
            returns = []
            for i in range(1, len(equity_curve)):
                daily_return = (equity_curve[i]['equity'] - equity_curve[i-1]['equity']) / equity_curve[i-1]['equity']
                returns.append(daily_return)
            
            if returns:
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                risk_free_rate = 0.03 / 252  # 假设年化无风险利率3%
                sharpe_ratio = (avg_return - risk_free_rate) / std_return * np.sqrt(252) if std_return > 0 else 0
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        return BacktestResult(
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            total_return_pct=total_return_pct,
            annualized_return=annualized_return,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            avg_profit_per_trade=avg_profit_per_trade,
            avg_holding_days=avg_holding_days,
            trades=trades,
            equity_curve=equity_curve
        )
    
    def print_report(self, result: BacktestResult):
        """
        打印回测报告
        
        Args:
            result: 回测结果
        """
        print(f"""
{'='*60}
回测报告
{'='*60}

【回测区间】
开始日期: {result.start_date.strftime('%Y-%m-%d')}
结束日期: {result.end_date.strftime('%Y-%m-%d')}
回测天数: {(result.end_date - result.start_date).days} 天

【资金状况】
初始资金: ¥{result.initial_capital:,.2f}
最终资金: ¥{result.final_capital:,.2f}
总收益: ¥{result.total_return:,.2f}
总收益率: {result.total_return_pct*100:.2f}%
年化收益率: {result.annualized_return*100:.2f}%

【风险指标】
最大回撤: ¥{result.max_drawdown:,.2f}
最大回撤比例: {result.max_drawdown_pct*100:.2f}%
夏普比率: {result.sharpe_ratio:.2f}

【交易统计】
总交易次数: {result.total_trades}
盈利次数: {result.winning_trades}
亏损次数: {result.losing_trades}
胜率: {result.win_rate*100:.1f}%
盈亏比: {result.profit_factor:.2f}
平均每笔收益: ¥{result.avg_profit_per_trade:,.2f}
平均持仓天数: {result.avg_holding_days:.1f} 天

【交易明细】
""")
        
        for i, trade in enumerate(result.trades, 1):
            profit_sign = "+" if trade.profit_loss > 0 else ""
            print(f"  {i}. {trade.entry_date.strftime('%Y-%m-%d')} 买入 @ ¥{trade.entry_price:.2f}")
            print(f"     {trade.exit_date.strftime('%Y-%m-%d')} 卖出 @ ¥{trade.exit_price:.2f}")
            print(f"     持仓 {trade.holding_days} 天, 收益: {profit_sign}¥{trade.profit_loss:.2f} ({profit_sign}{trade.profit_loss_pct*100:.1f}%)")
            print(f"     买入原因: {trade.entry_reason}")
            print(f"     卖出原因: {trade.exit_reason}")
            print()
        
        print(f"{'='*60}")


def demo_backtest():
    """
    回测示例
    """
    print("\n" + "="*60)
    print("股票力学模型回测示例")
    print("="*60)
    
    # 创建模拟价格数据
    np.random.seed(42)
    dates = pd.date_range(start='2025-01-01', periods=250, freq='B')
    
    # 模拟一个有趋势的股票
    base_price = 100
    prices_list = [base_price]
    trend = 0.0002  # 轻微上升趋势
    
    for i in range(249):
        noise = np.random.normal(0, 0.02)
        # 添加一些周期性波动
        cycle = 0.01 * np.sin(i / 20)
        change = trend + noise + cycle
        prices_list.append(prices_list[-1] * (1 + change))
    
    prices = np.array(prices_list)
    
    df = pd.DataFrame({
        'open': prices * (1 + np.random.uniform(-0.005, 0.005, len(prices))),
        'high': prices * (1 + np.random.uniform(0, 0.02, len(prices))),
        'low': prices * (1 - np.random.uniform(0, 0.02, len(prices))),
        'close': prices,
        'volume': np.random.uniform(100000, 500000, len(prices))
    }, index=dates)
    
    # 创建股票实体
    stock = StockEntity(
        symbol="TEST001",
        name="测试股票",
        market_cap=500,  # 500亿市值
        entity_type="stock"
    )
    
    # 添加一些长期和中期力
    stock.add_force(Force(
        name="行业景气度上升",
        magnitude=25,
        direction=ForceDirection.BULLISH,
        force_type=ForceType.LONG_TERM,
        start_date=datetime(2025, 1, 1),
        decay_rate=0.001,
        confidence=0.8,
        source="fundamental"
    ))
    
    stock.add_force(Force(
        name="政策利好",
        magnitude=20,
        direction=ForceDirection.BULLISH,
        force_type=ForceType.MID_TERM,
        start_date=datetime(2025, 3, 1),
        decay_rate=0.008,
        confidence=0.75,
        source="policy"
    ))
    
    # 添加一些阶段性的利空
    stock.add_force(Force(
        name="市场调整",
        magnitude=30,
        direction=ForceDirection.BEARISH,
        force_type=ForceType.SHORT_TERM,
        start_date=datetime(2025, 2, 15),
        decay_rate=0.1,
        confidence=0.7,
        source="market"
    ))
    
    # 创建策略
    strategy = ForceBasedStrategy(
        acceleration_buy_threshold=0.2,
        acceleration_sell_threshold=-0.2,
        force_ratio_buy_threshold=1.3,
        force_ratio_sell_threshold=0.8,
        min_holding_days=3,
        max_holding_days=20,
        stop_loss_pct=0.05,
        take_profit_pct=0.1
    )
    
    # 创建回测器
    backtester = Backtester(
        prices=df,
        stock=stock,
        strategy=strategy,
        initial_capital=100000
    )
    
    # 运行回测
    result = backtester.run(
        start_date=datetime(2025, 1, 15),
        end_date=datetime(2025, 10, 31)
    )
    
    # 打印报告
    backtester.print_report(result)
    
    return result


if __name__ == "__main__":
    demo_backtest()
