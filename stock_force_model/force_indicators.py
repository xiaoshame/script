# -*- coding: utf-8 -*-
"""
技术面力量指标计算模块

根据技术分析指标自动生成"短期力"
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass

from stock_force_model import Force, ForceDirection, ForceType, ForceFactory


@dataclass
class TechnicalSignal:
    """技术信号"""
    name: str
    direction: ForceDirection
    strength: float  # 0-100
    description: str


class TechnicalForceCalculator:
    """
    技术面力量计算器
    
    根据各种技术指标计算短期力量
    """
    
    def __init__(self, prices: pd.DataFrame):
        """
        初始化
        
        Args:
            prices: 价格数据DataFrame，需要包含 'open', 'high', 'low', 'close', 'volume' 列
                   index 应该是日期
        """
        self.prices = prices.copy()
        self._calculate_indicators()
    
    def _calculate_indicators(self):
        """计算各种技术指标"""
        df = self.prices
        
        # 移动平均线
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma10'] = df['close'].rolling(window=10).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma60'] = df['close'].rolling(window=60).mean()
        
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['signal']
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 布林带
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        df['bb_std'] = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + 2 * df['bb_std']
        df['bb_lower'] = df['bb_middle'] - 2 * df['bb_std']
        
        # KDJ
        low_min = df['low'].rolling(window=9).min()
        high_max = df['high'].rolling(window=9).max()
        rsv = (df['close'] - low_min) / (high_max - low_min) * 100
        df['k'] = rsv.ewm(com=2, adjust=False).mean()
        df['d'] = df['k'].ewm(com=2, adjust=False).mean()
        df['j'] = 3 * df['k'] - 2 * df['d']
        
        # 成交量相关
        df['volume_ma5'] = df['volume'].rolling(window=5).mean()
        df['volume_ma20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma20']
        
        # 动量指标
        df['momentum'] = df['close'].pct_change(periods=10) * 100
        
        # ATR (Average True Range)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=14).mean()
        
        self.prices = df
    
    def check_ma_cross(self, date: datetime) -> List[TechnicalSignal]:
        """
        检查均线交叉信号
        
        Args:
            date: 检查日期
            
        Returns:
            技术信号列表
        """
        signals = []
        
        try:
            idx = self.prices.index.get_loc(date)
            if idx < 2:
                return signals
        except KeyError:
            return signals
        
        curr = self.prices.iloc[idx]
        prev = self.prices.iloc[idx - 1]
        
        # MA5/MA10 金叉死叉
        if prev['ma5'] <= prev['ma10'] and curr['ma5'] > curr['ma10']:
            signals.append(TechnicalSignal(
                name="MA5上穿MA10金叉",
                direction=ForceDirection.BULLISH,
                strength=30,
                description="短期均线上穿中期均线，短期趋势向好"
            ))
        elif prev['ma5'] >= prev['ma10'] and curr['ma5'] < curr['ma10']:
            signals.append(TechnicalSignal(
                name="MA5下穿MA10死叉",
                direction=ForceDirection.BEARISH,
                strength=30,
                description="短期均线下穿中期均线，短期趋势转弱"
            ))
        
        # MA10/MA20 金叉死叉
        if prev['ma10'] <= prev['ma20'] and curr['ma10'] > curr['ma20']:
            signals.append(TechnicalSignal(
                name="MA10上穿MA20金叉",
                direction=ForceDirection.BULLISH,
                strength=40,
                description="中期均线向上交叉，中期趋势向好"
            ))
        elif prev['ma10'] >= prev['ma20'] and curr['ma10'] < curr['ma20']:
            signals.append(TechnicalSignal(
                name="MA10下穿MA20死叉",
                direction=ForceDirection.BEARISH,
                strength=40,
                description="中期均线向下交叉，中期趋势转弱"
            ))
        
        # 价格站上/跌破60日均线
        if prev['close'] <= prev['ma60'] and curr['close'] > curr['ma60']:
            signals.append(TechnicalSignal(
                name="股价站上60日均线",
                direction=ForceDirection.BULLISH,
                strength=50,
                description="价格突破长期均线，长期趋势可能反转"
            ))
        elif prev['close'] >= prev['ma60'] and curr['close'] < curr['ma60']:
            signals.append(TechnicalSignal(
                name="股价跌破60日均线",
                direction=ForceDirection.BEARISH,
                strength=50,
                description="价格跌破长期均线，长期趋势可能反转"
            ))
        
        return signals
    
    def check_macd_signal(self, date: datetime) -> List[TechnicalSignal]:
        """
        检查MACD信号
        
        Args:
            date: 检查日期
            
        Returns:
            技术信号列表
        """
        signals = []
        
        try:
            idx = self.prices.index.get_loc(date)
            if idx < 2:
                return signals
        except KeyError:
            return signals
        
        curr = self.prices.iloc[idx]
        prev = self.prices.iloc[idx - 1]
        
        # MACD金叉死叉
        if prev['macd'] <= prev['signal'] and curr['macd'] > curr['signal']:
            # 判断是在零轴上方还是下方
            if curr['macd'] > 0:
                signals.append(TechnicalSignal(
                    name="MACD零轴上方金叉",
                    direction=ForceDirection.BULLISH,
                    strength=45,
                    description="强势区域金叉，上涨动能强劲"
                ))
            else:
                signals.append(TechnicalSignal(
                    name="MACD零轴下方金叉",
                    direction=ForceDirection.BULLISH,
                    strength=35,
                    description="弱势区域金叉，可能是反弹信号"
                ))
        elif prev['macd'] >= prev['signal'] and curr['macd'] < curr['signal']:
            if curr['macd'] < 0:
                signals.append(TechnicalSignal(
                    name="MACD零轴下方死叉",
                    direction=ForceDirection.BEARISH,
                    strength=45,
                    description="弱势区域死叉，下跌动能强劲"
                ))
            else:
                signals.append(TechnicalSignal(
                    name="MACD零轴上方死叉",
                    direction=ForceDirection.BEARISH,
                    strength=35,
                    description="强势区域死叉，可能是回调信号"
                ))
        
        # MACD柱状图变化
        if len(self.prices) > idx + 1:
            hist_change = curr['macd_hist'] - prev['macd_hist']
            if abs(hist_change) > 0.1:
                if hist_change > 0:
                    signals.append(TechnicalSignal(
                        name="MACD动能增强",
                        direction=ForceDirection.BULLISH,
                        strength=min(abs(hist_change) * 100, 30),
                        description="MACD柱状图放大，动能增强"
                    ))
                else:
                    signals.append(TechnicalSignal(
                        name="MACD动能减弱",
                        direction=ForceDirection.BEARISH,
                        strength=min(abs(hist_change) * 100, 30),
                        description="MACD柱状图缩小，动能减弱"
                    ))
        
        return signals
    
    def check_rsi_signal(self, date: datetime) -> List[TechnicalSignal]:
        """
        检查RSI信号
        
        Args:
            date: 检查日期
            
        Returns:
            技术信号列表
        """
        signals = []
        
        try:
            idx = self.prices.index.get_loc(date)
            if idx < 1:
                return signals
        except KeyError:
            return signals
        
        curr = self.prices.iloc[idx]
        prev = self.prices.iloc[idx - 1]
        
        rsi = curr['rsi']
        
        # 超买超卖信号
        if rsi > 80:
            signals.append(TechnicalSignal(
                name="RSI超买",
                direction=ForceDirection.BEARISH,
                strength=min((rsi - 70) * 2, 40),
                description=f"RSI={rsi:.1f}，严重超买，注意回调风险"
            ))
        elif rsi > 70:
            signals.append(TechnicalSignal(
                name="RSI进入超买区",
                direction=ForceDirection.BEARISH,
                strength=20,
                description=f"RSI={rsi:.1f}，进入超买区域"
            ))
        elif rsi < 20:
            signals.append(TechnicalSignal(
                name="RSI超卖",
                direction=ForceDirection.BULLISH,
                strength=min((30 - rsi) * 2, 40),
                description=f"RSI={rsi:.1f}，严重超卖，注意反弹机会"
            ))
        elif rsi < 30:
            signals.append(TechnicalSignal(
                name="RSI进入超卖区",
                direction=ForceDirection.BULLISH,
                strength=20,
                description=f"RSI={rsi:.1f}，进入超卖区域"
            ))
        
        # RSI金叉死叉（从超买超卖区回归）
        if prev['rsi'] > 70 and curr['rsi'] <= 70:
            signals.append(TechnicalSignal(
                name="RSI离开超买区",
                direction=ForceDirection.BEARISH,
                strength=35,
                description="RSI从超买区回落，可能开始回调"
            ))
        elif prev['rsi'] < 30 and curr['rsi'] >= 30:
            signals.append(TechnicalSignal(
                name="RSI离开超卖区",
                direction=ForceDirection.BULLISH,
                strength=35,
                description="RSI从超卖区回升，可能开始反弹"
            ))
        
        return signals
    
    def check_kdj_signal(self, date: datetime) -> List[TechnicalSignal]:
        """
        检查KDJ信号
        
        Args:
            date: 检查日期
            
        Returns:
            技术信号列表
        """
        signals = []
        
        try:
            idx = self.prices.index.get_loc(date)
            if idx < 2:
                return signals
        except KeyError:
            return signals
        
        curr = self.prices.iloc[idx]
        prev = self.prices.iloc[idx - 1]
        
        # KDJ金叉死叉
        if prev['k'] <= prev['d'] and curr['k'] > curr['d']:
            strength = 30
            if curr['k'] < 20:
                strength = 45  # 低位金叉更有效
                desc = "KDJ低位金叉，超卖区反转信号"
            else:
                desc = "KDJ金叉"
            signals.append(TechnicalSignal(
                name="KDJ金叉",
                direction=ForceDirection.BULLISH,
                strength=strength,
                description=desc
            ))
        elif prev['k'] >= prev['d'] and curr['k'] < curr['d']:
            strength = 30
            if curr['k'] > 80:
                strength = 45  # 高位死叉更有效
                desc = "KDJ高位死叉，超买区反转信号"
            else:
                desc = "KDJ死叉"
            signals.append(TechnicalSignal(
                name="KDJ死叉",
                direction=ForceDirection.BEARISH,
                strength=strength,
                description=desc
            ))
        
        # J值极端信号
        if curr['j'] > 100:
            signals.append(TechnicalSignal(
                name="KDJ-J值超买",
                direction=ForceDirection.BEARISH,
                strength=min((curr['j'] - 100) / 2, 30),
                description=f"J值={curr['j']:.1f}，极度超买"
            ))
        elif curr['j'] < 0:
            signals.append(TechnicalSignal(
                name="KDJ-J值超卖",
                direction=ForceDirection.BULLISH,
                strength=min(abs(curr['j']) / 2, 30),
                description=f"J值={curr['j']:.1f}，极度超卖"
            ))
        
        return signals
    
    def check_bollinger_signal(self, date: datetime) -> List[TechnicalSignal]:
        """
        检查布林带信号
        
        Args:
            date: 检查日期
            
        Returns:
            技术信号列表
        """
        signals = []
        
        try:
            idx = self.prices.index.get_loc(date)
            if idx < 1:
                return signals
        except KeyError:
            return signals
        
        curr = self.prices.iloc[idx]
        prev = self.prices.iloc[idx - 1]
        
        close = curr['close']
        bb_upper = curr['bb_upper']
        bb_lower = curr['bb_lower']
        bb_middle = curr['bb_middle']
        
        # 突破上轨
        if prev['close'] <= prev['bb_upper'] and close > bb_upper:
            signals.append(TechnicalSignal(
                name="突破布林带上轨",
                direction=ForceDirection.BULLISH,
                strength=40,
                description="价格突破布林带上轨，强势上涨信号"
            ))
        # 跌破下轨
        elif prev['close'] >= prev['bb_lower'] and close < bb_lower:
            signals.append(TechnicalSignal(
                name="跌破布林带下轨",
                direction=ForceDirection.BEARISH,
                strength=40,
                description="价格跌破布林带下轨，强势下跌信号"
            ))
        
        # 布林带收窄（波动率降低，可能即将变盘）
        band_width = (bb_upper - bb_lower) / bb_middle
        if band_width < 0.05:
            signals.append(TechnicalSignal(
                name="布林带收窄",
                direction=ForceDirection.NEUTRAL,
                strength=20,
                description="布林带极度收窄，可能即将变盘"
            ))
        
        return signals
    
    def check_volume_signal(self, date: datetime) -> List[TechnicalSignal]:
        """
        检查成交量信号
        
        Args:
            date: 检查日期
            
        Returns:
            技术信号列表
        """
        signals = []
        
        try:
            idx = self.prices.index.get_loc(date)
            if idx < 1:
                return signals
        except KeyError:
            return signals
        
        curr = self.prices.iloc[idx]
        prev = self.prices.iloc[idx - 1]
        
        volume_ratio = curr['volume_ratio']
        price_change = (curr['close'] - prev['close']) / prev['close']
        
        # 放量上涨
        if volume_ratio > 2 and price_change > 0.02:
            signals.append(TechnicalSignal(
                name="放量上涨",
                direction=ForceDirection.BULLISH,
                strength=min(volume_ratio * 15, 50),
                description=f"成交量放大{volume_ratio:.1f}倍，上涨{price_change*100:.1f}%"
            ))
        # 放量下跌
        elif volume_ratio > 2 and price_change < -0.02:
            signals.append(TechnicalSignal(
                name="放量下跌",
                direction=ForceDirection.BEARISH,
                strength=min(volume_ratio * 15, 50),
                description=f"成交量放大{volume_ratio:.1f}倍，下跌{abs(price_change)*100:.1f}%"
            ))
        # 缩量上涨（可能上涨乏力）
        elif volume_ratio < 0.5 and price_change > 0.02:
            signals.append(TechnicalSignal(
                name="缩量上涨",
                direction=ForceDirection.BEARISH,
                strength=20,
                description="上涨但成交量萎缩，上涨动能不足"
            ))
        # 缩量下跌（可能下跌接近尾声）
        elif volume_ratio < 0.5 and price_change < -0.02:
            signals.append(TechnicalSignal(
                name="缩量下跌",
                direction=ForceDirection.BULLISH,
                strength=20,
                description="下跌但成交量萎缩，抛压减轻"
            ))
        
        # 天量信号（成交量异常放大）
        if volume_ratio > 5:
            signals.append(TechnicalSignal(
                name="成交量异常放大",
                direction=ForceDirection.NEUTRAL,
                strength=30,
                description=f"成交量是平均的{volume_ratio:.1f}倍，市场分歧巨大"
            ))
        
        return signals
    
    def check_volume_trend(self, date: datetime) -> List[TechnicalSignal]:
        """
        检查量能趋势信号（增强版）
        
        Args:
            date: 检查日期
            
        Returns:
            技术信号列表
        """
        signals = []
        
        try:
            idx = self.prices.index.get_loc(date)
            if idx < 5:
                return signals
        except KeyError:
            return signals
        
        # 获取最近5天数据
        recent = self.prices.iloc[idx-4:idx+1]
        curr = self.prices.iloc[idx]
        
        # 量能持续放大（连续3天量比>1.2）
        vol_ratios = recent['volume_ratio'].values
        if all(v > 1.2 for v in vol_ratios[-3:]):
            price_changes = recent['close'].pct_change().dropna()
            if price_changes.mean() > 0:
                signals.append(TechnicalSignal(
                    name="量能持续放大+上涨",
                    direction=ForceDirection.BULLISH,
                    strength=45,
                    description="连续放量上涨，资金持续流入"
                ))
            else:
                signals.append(TechnicalSignal(
                    name="量能持续放大+下跌",
                    direction=ForceDirection.BEARISH,
                    strength=45,
                    description="连续放量下跌，资金持续流出"
                ))
        
        # 量能萎缩后突然放大（底部放量信号）
        if vol_ratios[-2] < 0.7 and vol_ratios[-1] > 2:
            if curr['close'] > self.prices.iloc[idx-1]['close']:
                signals.append(TechnicalSignal(
                    name="缩量后放量上涨",
                    direction=ForceDirection.BULLISH,
                    strength=50,
                    description="量能萎缩后突然放大上涨，可能是启动信号"
                ))
        
        # 量价背离检测
        price_change_5d = (curr['close'] - self.prices.iloc[idx-4]['close']) / self.prices.iloc[idx-4]['close']
        vol_change_5d = (curr['volume'] - self.prices.iloc[idx-4]['volume']) / self.prices.iloc[idx-4]['volume']
        
        if price_change_5d > 0.05 and vol_change_5d < -0.2:
            signals.append(TechnicalSignal(
                name="价升量缩背离",
                direction=ForceDirection.BEARISH,
                strength=35,
                description="价格上涨但量能萎缩，上涨动能不足"
            ))
        elif price_change_5d < -0.05 and vol_change_5d < -0.2:
            signals.append(TechnicalSignal(
                name="价跌量缩",
                direction=ForceDirection.BULLISH,
                strength=25,
                description="价格下跌但量能萎缩，抛压减轻"
            ))
        
        return signals
    
    def check_macd_trend(self, date: datetime) -> List[TechnicalSignal]:
        """
        检查MACD趋势信号（增强版）
        
        Args:
            date: 检查日期
            
        Returns:
            技术信号列表
        """
        signals = []
        
        try:
            idx = self.prices.index.get_loc(date)
            if idx < 5:
                return signals
        except KeyError:
            return signals
        
        curr = self.prices.iloc[idx]
        recent = self.prices.iloc[idx-4:idx+1]
        
        # MACD连续向上（红柱持续放大）
        hist_values = recent['macd_hist'].values
        if all(hist_values[i] < hist_values[i+1] for i in range(len(hist_values)-1)):
            signals.append(TechnicalSignal(
                name="MACD柱连续放大",
                direction=ForceDirection.BULLISH,
                strength=40,
                description="MACD柱状图连续放大，动能持续增强"
            ))
        elif all(hist_values[i] > hist_values[i+1] for i in range(len(hist_values)-1)):
            signals.append(TechnicalSignal(
                name="MACD柱连续缩小",
                direction=ForceDirection.BEARISH,
                strength=40,
                description="MACD柱状图连续缩小，动能持续减弱"
            ))
        
        # MACD背离检测
        price_trend = curr['close'] > self.prices.iloc[idx-4]['close']
        macd_trend = curr['macd'] > self.prices.iloc[idx-4]['macd']
        
        if price_trend and not macd_trend:
            signals.append(TechnicalSignal(
                name="MACD顶背离",
                direction=ForceDirection.BEARISH,
                strength=55,
                description="价格创新高但MACD未创新高，顶背离信号"
            ))
        elif not price_trend and macd_trend:
            signals.append(TechnicalSignal(
                name="MACD底背离",
                direction=ForceDirection.BULLISH,
                strength=55,
                description="价格创新低但MACD未创新低，底背离信号"
            ))
        
        # MACD位置信号
        if curr['macd'] > 0 and curr['macd'] > curr['signal']:
            signals.append(TechnicalSignal(
                name="MACD多头排列",
                direction=ForceDirection.BULLISH,
                strength=25,
                description="MACD在零轴上方且DIF>DEA"
            ))
        elif curr['macd'] < 0 and curr['macd'] < curr['signal']:
            signals.append(TechnicalSignal(
                name="MACD空头排列",
                direction=ForceDirection.BEARISH,
                strength=25,
                description="MACD在零轴下方且DIF<DEA"
            ))
        
        return signals
    
    def check_kdj_trend(self, date: datetime) -> List[TechnicalSignal]:
        """
        检查KDJ趋势信号（增强版）
        
        Args:
            date: 检查日期
            
        Returns:
            技术信号列表
        """
        signals = []
        
        try:
            idx = self.prices.index.get_loc(date)
            if idx < 3:
                return signals
        except KeyError:
            return signals
        
        curr = self.prices.iloc[idx]
        prev = self.prices.iloc[idx-1]
        
        k, d, j = curr['k'], curr['d'], curr['j']
        
        # KDJ位置信号
        if k > 80 and d > 80:
            signals.append(TechnicalSignal(
                name="KDJ高位钝化",
                direction=ForceDirection.BEARISH,
                strength=30,
                description=f"K={k:.1f}, D={d:.1f}，高位钝化需警惕"
            ))
        elif k < 20 and d < 20:
            signals.append(TechnicalSignal(
                name="KDJ低位钝化",
                direction=ForceDirection.BULLISH,
                strength=30,
                description=f"K={k:.1f}, D={d:.1f}，低位钝化有反弹机会"
            ))
        
        # KDJ多头/空头排列
        if k > d > 50:
            signals.append(TechnicalSignal(
                name="KDJ多头排列",
                direction=ForceDirection.BULLISH,
                strength=20,
                description="K>D且均在50上方，多头趋势"
            ))
        elif k < d < 50:
            signals.append(TechnicalSignal(
                name="KDJ空头排列",
                direction=ForceDirection.BEARISH,
                strength=20,
                description="K<D且均在50下方，空头趋势"
            ))
        
        # J值趋势
        j_prev = prev['j']
        if j > j_prev and j > 50:
            signals.append(TechnicalSignal(
                name="KDJ-J值向上",
                direction=ForceDirection.BULLISH,
                strength=15,
                description=f"J值从{j_prev:.0f}上升到{j:.0f}"
            ))
        elif j < j_prev and j < 50:
            signals.append(TechnicalSignal(
                name="KDJ-J值向下",
                direction=ForceDirection.BEARISH,
                strength=15,
                description=f"J值从{j_prev:.0f}下降到{j:.0f}"
            ))
        
        return signals
    
    def check_rsi_trend(self, date: datetime) -> List[TechnicalSignal]:
        """
        检查RSI趋势信号（增强版）
        
        Args:
            date: 检查日期
            
        Returns:
            技术信号列表
        """
        signals = []
        
        try:
            idx = self.prices.index.get_loc(date)
            if idx < 5:
                return signals
        except KeyError:
            return signals
        
        curr = self.prices.iloc[idx]
        recent = self.prices.iloc[idx-4:idx+1]
        
        rsi = curr['rsi']
        
        # RSI趋势
        rsi_values = recent['rsi'].values
        rsi_trend = rsi_values[-1] - rsi_values[0]
        
        if rsi_trend > 10:
            signals.append(TechnicalSignal(
                name="RSI快速上升",
                direction=ForceDirection.BULLISH,
                strength=30,
                description=f"RSI从{rsi_values[0]:.0f}上升到{rsi:.0f}，动能增强"
            ))
        elif rsi_trend < -10:
            signals.append(TechnicalSignal(
                name="RSI快速下降",
                direction=ForceDirection.BEARISH,
                strength=30,
                description=f"RSI从{rsi_values[0]:.0f}下降到{rsi:.0f}，动能减弱"
            ))
        
        # RSI位置信号
        if 50 < rsi < 70:
            signals.append(TechnicalSignal(
                name="RSI强势区间",
                direction=ForceDirection.BULLISH,
                strength=15,
                description=f"RSI={rsi:.0f}，处于强势区间"
            ))
        elif 30 < rsi < 50:
            signals.append(TechnicalSignal(
                name="RSI弱势区间",
                direction=ForceDirection.BEARISH,
                strength=15,
                description=f"RSI={rsi:.0f}，处于弱势区间"
            ))
        
        # RSI背离检测
        price_trend = curr['close'] > self.prices.iloc[idx-4]['close']
        rsi_trend_dir = rsi > rsi_values[0]
        
        if price_trend and not rsi_trend_dir:
            signals.append(TechnicalSignal(
                name="RSI顶背离",
                direction=ForceDirection.BEARISH,
                strength=45,
                description="价格上涨但RSI下降，顶背离警告"
            ))
        elif not price_trend and rsi_trend_dir:
            signals.append(TechnicalSignal(
                name="RSI底背离",
                direction=ForceDirection.BULLISH,
                strength=45,
                description="价格下跌但RSI上升，底背离机会"
            ))
        
        return signals
    
    def get_all_signals(self, date: datetime) -> List[TechnicalSignal]:
        """
        获取所有技术信号
        
        Args:
            date: 检查日期
            
        Returns:
            所有技术信号列表
        """
        signals = []
        signals.extend(self.check_ma_cross(date))
        signals.extend(self.check_macd_signal(date))
        signals.extend(self.check_macd_trend(date))  # 新增MACD趋势
        signals.extend(self.check_rsi_signal(date))
        signals.extend(self.check_rsi_trend(date))   # 新增RSI趋势
        signals.extend(self.check_kdj_signal(date))
        signals.extend(self.check_kdj_trend(date))   # 新增KDJ趋势
        signals.extend(self.check_bollinger_signal(date))
        signals.extend(self.check_volume_signal(date))
        signals.extend(self.check_volume_trend(date))  # 新增量能趋势
        return signals
    
    def generate_forces(self, date: datetime) -> List[Force]:
        """
        根据技术信号生成力
        
        Args:
            date: 日期
            
        Returns:
            Force对象列表
        """
        signals = self.get_all_signals(date)
        forces = []
        
        for signal in signals:
            if signal.direction == ForceDirection.NEUTRAL:
                continue
            
            force = ForceFactory.create_technical_force(
                name=signal.name,
                magnitude=signal.strength,
                direction=signal.direction,
                start_date=date
            )
            forces.append(force)
        
        return forces


class FundamentalForceCalculator:
    """
    基本面力量计算器
    
    根据财务数据计算中期力量
    """
    
    @staticmethod
    def analyze_earnings(eps_growth: float, revenue_growth: float,
                        date: datetime) -> List[Force]:
        """
        分析财报数据生成力
        
        Args:
            eps_growth: EPS同比增长率
            revenue_growth: 营收同比增长率
            date: 财报发布日期
            
        Returns:
            Force列表
        """
        forces = []
        
        # EPS增长分析
        if eps_growth > 0.5:  # 增长超过50%
            forces.append(Force(
                name=f"EPS大幅增长{eps_growth*100:.0f}%",
                magnitude=min(eps_growth * 60, 60),
                direction=ForceDirection.BULLISH,
                force_type=ForceType.MID_TERM,
                start_date=date,
                decay_rate=0.005,
                confidence=0.85,
                source="fundamental"
            ))
        elif eps_growth > 0.2:  # 增长20%-50%
            forces.append(Force(
                name=f"EPS稳健增长{eps_growth*100:.0f}%",
                magnitude=eps_growth * 80,
                direction=ForceDirection.BULLISH,
                force_type=ForceType.MID_TERM,
                start_date=date,
                decay_rate=0.006,
                confidence=0.8,
                source="fundamental"
            ))
        elif eps_growth < -0.2:  # 下滑超过20%
            forces.append(Force(
                name=f"EPS下滑{abs(eps_growth)*100:.0f}%",
                magnitude=min(abs(eps_growth) * 80, 60),
                direction=ForceDirection.BEARISH,
                force_type=ForceType.MID_TERM,
                start_date=date,
                decay_rate=0.005,
                confidence=0.85,
                source="fundamental"
            ))
        
        # 营收增长分析
        if revenue_growth > 0.3:
            forces.append(Force(
                name=f"营收高速增长{revenue_growth*100:.0f}%",
                magnitude=min(revenue_growth * 50, 45),
                direction=ForceDirection.BULLISH,
                force_type=ForceType.MID_TERM,
                start_date=date,
                decay_rate=0.004,
                confidence=0.8,
                source="fundamental"
            ))
        elif revenue_growth < -0.1:
            forces.append(Force(
                name=f"营收下滑{abs(revenue_growth)*100:.0f}%",
                magnitude=min(abs(revenue_growth) * 60, 40),
                direction=ForceDirection.BEARISH,
                force_type=ForceType.MID_TERM,
                start_date=date,
                decay_rate=0.004,
                confidence=0.8,
                source="fundamental"
            ))
        
        return forces
    
    @staticmethod
    def analyze_valuation(pe_ratio: float, pb_ratio: float,
                         industry_avg_pe: float, industry_avg_pb: float,
                         date: datetime) -> List[Force]:
        """
        分析估值水平
        
        Args:
            pe_ratio: 市盈率
            pb_ratio: 市净率
            industry_avg_pe: 行业平均市盈率
            industry_avg_pb: 行业平均市净率
            date: 分析日期
            
        Returns:
            Force列表
        """
        forces = []
        
        if industry_avg_pe > 0 and pe_ratio > 0:
            pe_premium = (pe_ratio - industry_avg_pe) / industry_avg_pe
            
            if pe_premium > 0.5:  # 估值溢价超过50%
                forces.append(Force(
                    name=f"估值过高(PE溢价{pe_premium*100:.0f}%)",
                    magnitude=min(pe_premium * 30, 40),
                    direction=ForceDirection.BEARISH,
                    force_type=ForceType.MID_TERM,
                    start_date=date,
                    decay_rate=0.003,
                    confidence=0.7,
                    source="fundamental"
                ))
            elif pe_premium < -0.3:  # 估值折价超过30%
                forces.append(Force(
                    name=f"估值偏低(PE折价{abs(pe_premium)*100:.0f}%)",
                    magnitude=min(abs(pe_premium) * 40, 35),
                    direction=ForceDirection.BULLISH,
                    force_type=ForceType.MID_TERM,
                    start_date=date,
                    decay_rate=0.003,
                    confidence=0.7,
                    source="fundamental"
                ))
        
        return forces


class SentimentForceCalculator:
    """
    市场情绪力量计算器
    
    根据市场情绪指标计算短期力量
    """
    
    @staticmethod
    def analyze_sentiment(fear_greed_index: float,
                         margin_balance_change: float,
                         northbound_flow: float,
                         date: datetime) -> List[Force]:
        """
        分析市场情绪
        
        Args:
            fear_greed_index: 恐惧贪婪指数 (0-100)
            margin_balance_change: 融资余额变化率
            northbound_flow: 北向资金净流入（亿元）
            date: 分析日期
            
        Returns:
            Force列表
        """
        forces = []
        
        # 恐惧贪婪指数
        if fear_greed_index > 80:
            forces.append(Force(
                name="市场极度贪婪",
                magnitude=min((fear_greed_index - 70) * 2, 40),
                direction=ForceDirection.BEARISH,
                force_type=ForceType.SHORT_TERM,
                start_date=date,
                decay_rate=0.15,
                confidence=0.65,
                source="sentiment"
            ))
        elif fear_greed_index < 20:
            forces.append(Force(
                name="市场极度恐惧",
                magnitude=min((30 - fear_greed_index) * 2, 40),
                direction=ForceDirection.BULLISH,
                force_type=ForceType.SHORT_TERM,
                start_date=date,
                decay_rate=0.15,
                confidence=0.65,
                source="sentiment"
            ))
        
        # 北向资金
        if northbound_flow > 100:
            forces.append(Force(
                name=f"北向资金大幅流入{northbound_flow:.0f}亿",
                magnitude=min(northbound_flow / 5, 50),
                direction=ForceDirection.BULLISH,
                force_type=ForceType.SHORT_TERM,
                start_date=date,
                decay_rate=0.1,
                confidence=0.75,
                source="capital_flow"
            ))
        elif northbound_flow < -100:
            forces.append(Force(
                name=f"北向资金大幅流出{abs(northbound_flow):.0f}亿",
                magnitude=min(abs(northbound_flow) / 5, 50),
                direction=ForceDirection.BEARISH,
                force_type=ForceType.SHORT_TERM,
                start_date=date,
                decay_rate=0.1,
                confidence=0.75,
                source="capital_flow"
            ))
        
        # 融资余额
        if margin_balance_change > 0.05:
            forces.append(Force(
                name="融资余额大幅增加",
                magnitude=min(margin_balance_change * 300, 30),
                direction=ForceDirection.BULLISH,
                force_type=ForceType.SHORT_TERM,
                start_date=date,
                decay_rate=0.08,
                confidence=0.7,
                source="capital_flow"
            ))
        elif margin_balance_change < -0.05:
            forces.append(Force(
                name="融资余额大幅减少",
                magnitude=min(abs(margin_balance_change) * 300, 30),
                direction=ForceDirection.BEARISH,
                force_type=ForceType.SHORT_TERM,
                start_date=date,
                decay_rate=0.08,
                confidence=0.7,
                source="capital_flow"
            ))
        
        return forces


if __name__ == "__main__":
    # 测试示例
    print("技术面力量计算器测试")
    
    # 创建模拟数据
    dates = pd.date_range(start='2025-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # 模拟价格数据
    base_price = 100
    prices = [base_price]
    for i in range(99):
        change = np.random.normal(0, 2)
        prices.append(prices[-1] * (1 + change / 100))
    
    df = pd.DataFrame({
        'open': [p * (1 + np.random.uniform(-0.01, 0.01)) for p in prices],
        'high': [p * (1 + np.random.uniform(0, 0.02)) for p in prices],
        'low': [p * (1 - np.random.uniform(0, 0.02)) for p in prices],
        'close': prices,
        'volume': [np.random.uniform(100000, 500000) for _ in range(100)]
    }, index=dates)
    
    # 初始化计算器
    calculator = TechnicalForceCalculator(df)
    
    # 获取最后一天的信号
    test_date = dates[-1]
    signals = calculator.get_all_signals(test_date)
    
    print(f"\n日期: {test_date.strftime('%Y-%m-%d')}")
    print("-" * 50)
    for signal in signals:
        direction = "利多" if signal.direction == ForceDirection.BULLISH else "利空"
        print(f"  [{direction}] {signal.name}: 强度 {signal.strength:.0f}")
        print(f"         {signal.description}")
    
    # 生成力
    forces = calculator.generate_forces(test_date)
    print(f"\n生成了 {len(forces)} 个技术面力量")
