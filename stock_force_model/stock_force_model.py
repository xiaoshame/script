# -*- coding: utf-8 -*-
"""
股票力学量化模型 (Stock Force Quantitative Model)

基于牛顿第二定律的股票分析框架：
- ma = F合 (质量 × 加速度 = 合力)
- F合 = F分1 + F分2 + ... + F分N (合力 = 各分力之和)

其中：
- m: 市值 (Market Cap)
- a: 价格变化加速度 (Price Acceleration)
- F: 市场消息面的力 (Market Force from News/Events)

力的分类：
- 长期力 (Long-term Force): 作用时间 > 1年，如美联储利率政策、行业周期
- 中期力 (Mid-term Force): 作用时间 1个月 ~ 1年，如季度财报、行业政策
- 短期力 (Short-term Force): 作用时间 < 1个月，如突发新闻、技术面信号
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from abc import ABC, abstractmethod
import json


class ForceType(Enum):
    """力的类型枚举"""
    LONG_TERM = "long_term"      # 长期力 (>1年)
    MID_TERM = "mid_term"        # 中期力 (1个月~1年)
    SHORT_TERM = "short_term"    # 短期力 (<1个月)


class ForceDirection(Enum):
    """力的方向枚举"""
    BULLISH = 1      # 利多（向上的力）
    BEARISH = -1     # 利空（向下的力）
    NEUTRAL = 0      # 中性


@dataclass
class Force:
    """
    力的基本数据结构
    
    Attributes:
        name: 力的名称/来源描述
        magnitude: 力的大小 (绝对值，0-100的标准化值)
        direction: 力的方向 (利多/利空/中性)
        force_type: 力的类型 (长期/中期/短期)
        start_date: 力开始作用的日期
        decay_rate: 衰减率 (每天衰减的比例，0-1之间)
        confidence: 对这个力判断的置信度 (0-1)
        source: 消息来源
    """
    name: str
    magnitude: float
    direction: ForceDirection
    force_type: ForceType
    start_date: datetime
    decay_rate: float = 0.0
    confidence: float = 1.0
    source: str = ""
    
    def get_current_magnitude(self, current_date: datetime) -> float:
        """
        计算力在当前日期的实际大小（考虑时间衰减）
        
        Args:
            current_date: 当前日期
            
        Returns:
            衰减后的力的大小
        """
        # 确保两个datetime都是naive（无时区信息）
        current = current_date.replace(tzinfo=None) if current_date.tzinfo else current_date
        start = self.start_date.replace(tzinfo=None) if self.start_date.tzinfo else self.start_date
        
        days_passed = (current - start).days
        if days_passed < 0:
            return 0.0  # 力还未开始作用
        
        # 指数衰减模型: F(t) = F0 * e^(-λt)
        decay_factor = np.exp(-self.decay_rate * days_passed)
        return self.magnitude * decay_factor * self.confidence
    
    def get_vector_force(self, current_date: datetime) -> float:
        """
        获取力的向量值（带方向）
        
        Args:
            current_date: 当前日期
            
        Returns:
            带方向的力值（正数表示利多，负数表示利空）
        """
        return self.get_current_magnitude(current_date) * self.direction.value
    
    def is_active(self, current_date: datetime, threshold: float = 0.01) -> bool:
        """
        判断力是否仍然活跃
        
        Args:
            current_date: 当前日期
            threshold: 力的最小阈值
            
        Returns:
            是否活跃
        """
        return self.get_current_magnitude(current_date) >= threshold
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "magnitude": self.magnitude,
            "direction": self.direction.name,
            "force_type": self.force_type.value,
            "start_date": self.start_date.isoformat(),
            "decay_rate": self.decay_rate,
            "confidence": self.confidence,
            "source": self.source
        }


class ForceFactory:
    """力的工厂类，用于创建不同类型的力"""
    
    # 默认衰减率配置
    DEFAULT_DECAY_RATES = {
        ForceType.LONG_TERM: 0.001,    # 长期力衰减慢，约693天半衰期
        ForceType.MID_TERM: 0.01,      # 中期力中等衰减，约69天半衰期
        ForceType.SHORT_TERM: 0.1,     # 短期力衰减快，约7天半衰期
    }
    
    @classmethod
    def create_policy_force(cls, name: str, magnitude: float, 
                           direction: ForceDirection, 
                           start_date: datetime,
                           is_central_bank: bool = False) -> Force:
        """
        创建政策类力（如美联储降息、行业政策等）
        
        Args:
            name: 政策名称
            magnitude: 力度大小
            direction: 方向
            start_date: 开始日期
            is_central_bank: 是否是央行政策
            
        Returns:
            Force对象
        """
        force_type = ForceType.LONG_TERM if is_central_bank else ForceType.MID_TERM
        decay_rate = cls.DEFAULT_DECAY_RATES[force_type]
        
        return Force(
            name=name,
            magnitude=magnitude,
            direction=direction,
            force_type=force_type,
            start_date=start_date,
            decay_rate=decay_rate,
            confidence=0.9,
            source="policy"
        )
    
    @classmethod
    def create_news_force(cls, name: str, magnitude: float,
                         direction: ForceDirection,
                         start_date: datetime,
                         is_major_event: bool = False) -> Force:
        """
        创建新闻事件类力（如公司丑闻、重大利好等）
        
        Args:
            name: 新闻描述
            magnitude: 影响力度
            direction: 方向
            start_date: 发生日期
            is_major_event: 是否是重大事件
            
        Returns:
            Force对象
        """
        if is_major_event:
            force_type = ForceType.MID_TERM
            decay_rate = 0.02
        else:
            force_type = ForceType.SHORT_TERM
            decay_rate = cls.DEFAULT_DECAY_RATES[ForceType.SHORT_TERM]
        
        return Force(
            name=name,
            magnitude=magnitude,
            direction=direction,
            force_type=force_type,
            start_date=start_date,
            decay_rate=decay_rate,
            confidence=0.7,
            source="news"
        )
    
    @classmethod
    def create_technical_force(cls, name: str, magnitude: float,
                              direction: ForceDirection,
                              start_date: datetime) -> Force:
        """
        创建技术面类力（如均线突破、MACD金叉等）
        
        Args:
            name: 技术指标名称
            magnitude: 信号强度
            direction: 方向
            start_date: 信号日期
            
        Returns:
            Force对象
        """
        return Force(
            name=name,
            magnitude=magnitude,
            direction=direction,
            force_type=ForceType.SHORT_TERM,
            start_date=start_date,
            decay_rate=0.15,  # 技术信号衰减较快
            confidence=0.6,
            source="technical"
        )
    
    @classmethod
    def create_fundamental_force(cls, name: str, magnitude: float,
                                 direction: ForceDirection,
                                 start_date: datetime) -> Force:
        """
        创建基本面类力（如财报、估值变化等）
        
        Args:
            name: 基本面因素名称
            magnitude: 影响力度
            direction: 方向
            start_date: 发生日期
            
        Returns:
            Force对象
        """
        return Force(
            name=name,
            magnitude=magnitude,
            direction=direction,
            force_type=ForceType.MID_TERM,
            start_date=start_date,
            decay_rate=0.005,  # 基本面影响持续时间长
            confidence=0.8,
            source="fundamental"
        )


@dataclass
class StockEntity:
    """
    股票实体类（可以是个股、行业或指数）
    
    Attributes:
        symbol: 股票代码
        name: 名称
        market_cap: 市值 (单位：亿元)
        entity_type: 实体类型 (stock/sector/index)
        forces: 作用于该实体的所有力
    """
    symbol: str
    name: str
    market_cap: float  # 市值，单位：亿元
    entity_type: str = "stock"  # stock/sector/index
    forces: List[Force] = field(default_factory=list)
    
    def add_force(self, force: Force):
        """添加一个力"""
        self.forces.append(force)
    
    def remove_inactive_forces(self, current_date: datetime, threshold: float = 0.01):
        """移除已经衰减到无效的力"""
        self.forces = [f for f in self.forces if f.is_active(current_date, threshold)]
    
    def get_forces_by_type(self, force_type: ForceType) -> List[Force]:
        """按类型获取力"""
        return [f for f in self.forces if f.force_type == force_type]


class StockForceAnalyzer:
    """
    股票力学分析器
    
    核心分析类，实现 F = ma 的股票版本：
    - 计算合力
    - 根据市值计算加速度
    - 预测价格走势
    """
    
    def __init__(self, stock: StockEntity):
        """
        初始化分析器
        
        Args:
            stock: 股票实体
        """
        self.stock = stock
        
    def calculate_net_force(self, current_date: datetime) -> float:
        """
        计算合力 F合 = ΣF分i
        
        Args:
            current_date: 当前日期
            
        Returns:
            合力值（正数表示向上，负数表示向下）
        """
        net_force = sum(
            force.get_vector_force(current_date) 
            for force in self.stock.forces
        )
        return net_force
    
    def calculate_force_by_type(self, current_date: datetime) -> Dict[ForceType, float]:
        """
        分类计算各类型力的合力
        
        Args:
            current_date: 当前日期
            
        Returns:
            各类型力的合力字典
        """
        result = {}
        for force_type in ForceType:
            forces = self.stock.get_forces_by_type(force_type)
            type_force = sum(f.get_vector_force(current_date) for f in forces)
            result[force_type] = type_force
        return result
    
    def calculate_acceleration(self, current_date: datetime) -> float:
        """
        计算加速度 a = F合 / m
        
        这里使用标准化的加速度，将市值转换为一个系数
        市值越大，同样的力产生的加速度越小（大盘股更难推动）
        
        Args:
            current_date: 当前日期
            
        Returns:
            加速度值（可以理解为预期的日涨跌幅百分比）
        """
        net_force = self.calculate_net_force(current_date)
        
        # 使用对数市值作为"质量"，使得计算更加合理
        # 市值越大，"惯性"越大，越难被推动
        log_market_cap = np.log10(self.stock.market_cap + 1)
        
        # 标准化系数，将结果调整到合理的涨跌幅范围
        normalization_factor = 0.01
        
        acceleration = (net_force / log_market_cap) * normalization_factor
        return acceleration
    
    def get_force_decomposition(self, current_date: datetime) -> Dict:
        """
        获取力的正交分解结果
        
        类似物理中的受力分析，将所有力分解并汇总
        
        Args:
            current_date: 当前日期
            
        Returns:
            力的分解结果
        """
        bullish_forces = []
        bearish_forces = []
        
        for force in self.stock.forces:
            current_mag = force.get_current_magnitude(current_date)
            if current_mag < 0.01:
                continue
                
            force_info = {
                "name": force.name,
                "magnitude": round(current_mag, 2),
                "type": force.force_type.value,
                "source": force.source
            }
            
            if force.direction == ForceDirection.BULLISH:
                bullish_forces.append(force_info)
            elif force.direction == ForceDirection.BEARISH:
                bearish_forces.append(force_info)
        
        # 按力的大小排序
        bullish_forces.sort(key=lambda x: x["magnitude"], reverse=True)
        bearish_forces.sort(key=lambda x: x["magnitude"], reverse=True)
        
        total_bullish = sum(f["magnitude"] for f in bullish_forces)
        total_bearish = sum(f["magnitude"] for f in bearish_forces)
        
        return {
            "bullish_forces": bullish_forces,
            "bearish_forces": bearish_forces,
            "total_bullish": round(total_bullish, 2),
            "total_bearish": round(total_bearish, 2),
            "net_force": round(total_bullish - total_bearish, 2),
            "force_ratio": round(total_bullish / total_bearish, 2) if total_bearish > 0 else float('inf')
        }
    
    def predict_trend(self, current_date: datetime, days: int = 5) -> List[Dict]:
        """
        基于力学模型预测未来趋势
        
        Args:
            current_date: 当前日期
            days: 预测天数
            
        Returns:
            每天的预测结果列表
        """
        predictions = []
        
        for i in range(days):
            # 预测从明天开始，所以用 i+1
            date = current_date + timedelta(days=i+1)
            
            # 计算当天的各项指标
            net_force = self.calculate_net_force(date)
            acceleration = self.calculate_acceleration(date)
            force_by_type = self.calculate_force_by_type(date)
            
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
            
            predictions.append({
                "date": date.strftime("%Y-%m-%d"),
                "net_force": round(net_force, 2),
                "acceleration": round(acceleration, 4),
                "expected_change_pct": round(acceleration, 2),
                "trend": trend,
                "force_breakdown": {
                    "long_term": round(force_by_type[ForceType.LONG_TERM], 2),
                    "mid_term": round(force_by_type[ForceType.MID_TERM], 2),
                    "short_term": round(force_by_type[ForceType.SHORT_TERM], 2)
                }
            })
        
        return predictions
    
    def generate_report(self, current_date: datetime) -> str:
        """
        生成分析报告
        
        Args:
            current_date: 当前日期
            
        Returns:
            分析报告文本
        """
        decomposition = self.get_force_decomposition(current_date)
        acceleration = self.calculate_acceleration(current_date)
        force_by_type = self.calculate_force_by_type(current_date)
        predictions = self.predict_trend(current_date)
        
        report = f"""
{'='*60}
股票力学分析报告
{'='*60}

【基本信息】
股票代码: {self.stock.symbol}
股票名称: {self.stock.name}
当前市值: {self.stock.market_cap:.2f} 亿元
实体类型: {self.stock.entity_type}
分析日期: {current_date.strftime("%Y-%m-%d")}

【受力分析】
当前作用力数量: {len(self.stock.forces)}

利多力量 (向上):
"""
        for f in decomposition["bullish_forces"][:5]:
            report += f"  [+] {f['name']}: {f['magnitude']} ({f['type']}, {f['source']})\n"
        report += f"  总利多力: {decomposition['total_bullish']}\n"
        
        report += f"""
利空力量 (向下):
"""
        for f in decomposition["bearish_forces"][:5]:
            report += f"  [-] {f['name']}: {f['magnitude']} ({f['type']}, {f['source']})\n"
        report += f"  总利空力: {decomposition['total_bearish']}\n"
        
        report += f"""
【力的合成】
合力 F合: {decomposition['net_force']}
多空比: {decomposition['force_ratio']:.2f}

【分类力量】
长期力: {force_by_type[ForceType.LONG_TERM]:.2f}
中期力: {force_by_type[ForceType.MID_TERM]:.2f}
短期力: {force_by_type[ForceType.SHORT_TERM]:.2f}

【加速度计算】
a = F合 / log(m) = {decomposition['net_force']:.2f} / {np.log10(self.stock.market_cap + 1):.2f}
当前加速度: {acceleration:.4f}
预期日涨跌幅: {acceleration:.2f}%

【趋势预测】
"""
        for pred in predictions:
            report += f"  {pred['date']}: {pred['trend']} (预期变化: {pred['expected_change_pct']:.2f}%)\n"
        
        report += f"""
{'='*60}
"""
        return report


class VolumeForceCalculator:
    """
    成交量力分析器
    
    成交量越大，说明分歧越大，各方力量博弈越激烈
    """
    
    @staticmethod
    def calculate_volume_divergence(volumes: List[float], 
                                    price_changes: List[float]) -> float:
        """
        计算量价分歧度
        
        Args:
            volumes: 成交量序列
            price_changes: 价格变化序列
            
        Returns:
            分歧度指标 (0-1之间，越大分歧越大)
        """
        if len(volumes) < 2 or len(price_changes) < 2:
            return 0.0
        
        # 计算成交量变化率
        vol_changes = np.diff(volumes) / np.array(volumes[:-1])
        
        # 量价背离程度
        # 如果成交量放大但价格变化小，说明分歧大
        avg_vol_change = np.mean(np.abs(vol_changes))
        avg_price_change = np.mean(np.abs(price_changes[1:]))
        
        if avg_price_change == 0:
            return 1.0
        
        divergence = min(avg_vol_change / (avg_price_change + 0.001), 1.0)
        return divergence
    
    @staticmethod
    def estimate_force_count(volume: float, avg_volume: float) -> int:
        """
        估算作用力的数量
        
        成交量越大，参与的力量越多
        
        Args:
            volume: 当日成交量
            avg_volume: 平均成交量
            
        Returns:
            估计的力量数量
        """
        if avg_volume == 0:
            return 1
        
        ratio = volume / avg_volume
        # 基础力量数 + 额外力量
        base_forces = 3
        additional_forces = int(ratio * 5)
        
        return base_forces + additional_forces


# ==================== 示例使用 ====================

def demo_single_stock_analysis():
    """
    示例：单个股票的力学分析
    """
    print("\n" + "="*60)
    print("示例1: 单个股票的力学分析")
    print("="*60)
    
    # 创建一个股票实体（以贵州茅台为例）
    stock = StockEntity(
        symbol="600519",
        name="贵州茅台",
        market_cap=20000,  # 2万亿市值
        entity_type="stock"
    )
    
    current_date = datetime(2026, 1, 12)
    
    # 添加各种作用力
    
    # 1. 长期力：美联储降息周期
    stock.add_force(ForceFactory.create_policy_force(
        name="美联储降息周期",
        magnitude=30,
        direction=ForceDirection.BULLISH,
        start_date=datetime(2025, 9, 1),
        is_central_bank=True
    ))
    
    # 2. 中期力：白酒行业复苏预期
    stock.add_force(ForceFactory.create_fundamental_force(
        name="白酒行业复苏预期",
        magnitude=25,
        direction=ForceDirection.BULLISH,
        start_date=datetime(2025, 11, 1)
    ))
    
    # 3. 中期力：季度财报超预期
    stock.add_force(ForceFactory.create_fundamental_force(
        name="Q3财报超预期",
        magnitude=20,
        direction=ForceDirection.BULLISH,
        start_date=datetime(2025, 10, 28)
    ))
    
    # 4. 短期力：技术面MACD金叉
    stock.add_force(ForceFactory.create_technical_force(
        name="MACD金叉",
        magnitude=15,
        direction=ForceDirection.BULLISH,
        start_date=datetime(2026, 1, 10)
    ))
    
    # 5. 短期利空：高管减持
    stock.add_force(ForceFactory.create_news_force(
        name="高管减持公告",
        magnitude=10,
        direction=ForceDirection.BEARISH,
        start_date=datetime(2026, 1, 8),
        is_major_event=False
    ))
    
    # 6. 中期利空：消费降级担忧
    stock.add_force(Force(
        name="消费降级担忧",
        magnitude=15,
        direction=ForceDirection.BEARISH,
        force_type=ForceType.MID_TERM,
        start_date=datetime(2025, 12, 1),
        decay_rate=0.008,
        confidence=0.6,
        source="market_sentiment"
    ))
    
    # 创建分析器
    analyzer = StockForceAnalyzer(stock)
    
    # 生成报告
    report = analyzer.generate_report(current_date)
    print(report)
    
    return stock, analyzer


def demo_sector_analysis():
    """
    示例：行业指数的力学分析
    """
    print("\n" + "="*60)
    print("示例2: 行业指数的力学分析")
    print("="*60)
    
    # 创建新能源行业指数
    sector = StockEntity(
        symbol="BK0478",
        name="新能源汽车板块",
        market_cap=50000,  # 5万亿市值
        entity_type="sector"
    )
    
    current_date = datetime(2026, 1, 12)
    
    # 添加行业级别的力
    
    # 长期力：双碳政策支持
    sector.add_force(Force(
        name="双碳政策支持",
        magnitude=40,
        direction=ForceDirection.BULLISH,
        force_type=ForceType.LONG_TERM,
        start_date=datetime(2024, 1, 1),
        decay_rate=0.0005,
        confidence=0.95,
        source="policy"
    ))
    
    # 中期力：欧洲碳排放法规
    sector.add_force(Force(
        name="欧洲碳排放法规收紧",
        magnitude=25,
        direction=ForceDirection.BULLISH,
        force_type=ForceType.MID_TERM,
        start_date=datetime(2025, 10, 1),
        decay_rate=0.005,
        confidence=0.8,
        source="policy"
    ))
    
    # 短期利空：补贴退坡
    sector.add_force(Force(
        name="新能源车补贴退坡",
        magnitude=20,
        direction=ForceDirection.BEARISH,
        force_type=ForceType.SHORT_TERM,
        start_date=datetime(2026, 1, 1),
        decay_rate=0.05,
        confidence=0.9,
        source="policy"
    ))
    
    # 中期力：电池成本下降
    sector.add_force(Force(
        name="电池成本持续下降",
        magnitude=30,
        direction=ForceDirection.BULLISH,
        force_type=ForceType.MID_TERM,
        start_date=datetime(2025, 6, 1),
        decay_rate=0.003,
        confidence=0.85,
        source="fundamental"
    ))
    
    analyzer = StockForceAnalyzer(sector)
    report = analyzer.generate_report(current_date)
    print(report)
    
    return sector, analyzer


def demo_index_analysis():
    """
    示例：大盘指数的力学分析
    """
    print("\n" + "="*60)
    print("示例3: 大盘指数的力学分析")
    print("="*60)
    
    # 创建上证指数
    index = StockEntity(
        symbol="000001",
        name="上证指数",
        market_cap=500000,  # 50万亿市值
        entity_type="index"
    )
    
    current_date = datetime(2026, 1, 12)
    
    # 宏观经济层面的力
    
    # 长期力：经济复苏预期
    index.add_force(Force(
        name="中国经济复苏预期",
        magnitude=35,
        direction=ForceDirection.BULLISH,
        force_type=ForceType.LONG_TERM,
        start_date=datetime(2025, 3, 1),
        decay_rate=0.001,
        confidence=0.7,
        source="macro"
    ))
    
    # 长期力：美联储降息周期
    index.add_force(Force(
        name="全球流动性宽松",
        magnitude=30,
        direction=ForceDirection.BULLISH,
        force_type=ForceType.LONG_TERM,
        start_date=datetime(2025, 9, 1),
        decay_rate=0.001,
        confidence=0.85,
        source="policy"
    ))
    
    # 中期力：外资流入
    index.add_force(Force(
        name="北向资金持续流入",
        magnitude=20,
        direction=ForceDirection.BULLISH,
        force_type=ForceType.MID_TERM,
        start_date=datetime(2025, 11, 1),
        decay_rate=0.01,
        confidence=0.75,
        source="capital_flow"
    ))
    
    # 中期利空：地缘政治风险
    index.add_force(Force(
        name="地缘政治不确定性",
        magnitude=25,
        direction=ForceDirection.BEARISH,
        force_type=ForceType.MID_TERM,
        start_date=datetime(2025, 8, 1),
        decay_rate=0.005,
        confidence=0.6,
        source="geopolitical"
    ))
    
    # 短期力：市场情绪
    index.add_force(Force(
        name="节前资金面紧张",
        magnitude=15,
        direction=ForceDirection.BEARISH,
        force_type=ForceType.SHORT_TERM,
        start_date=datetime(2026, 1, 10),
        decay_rate=0.2,
        confidence=0.8,
        source="market_sentiment"
    ))
    
    analyzer = StockForceAnalyzer(index)
    report = analyzer.generate_report(current_date)
    print(report)
    
    return index, analyzer


def demo_force_comparison():
    """
    示例：对比不同时间周期力的影响
    """
    print("\n" + "="*60)
    print("示例4: 不同时间周期力的影响对比")
    print("="*60)
    
    stock = StockEntity(
        symbol="TEST",
        name="测试股票",
        market_cap=1000,
        entity_type="stock"
    )
    
    start_date = datetime(2026, 1, 1)
    
    # 添加三种不同类型的力，初始大小相同
    stock.add_force(Force(
        name="长期力示例",
        magnitude=50,
        direction=ForceDirection.BULLISH,
        force_type=ForceType.LONG_TERM,
        start_date=start_date,
        decay_rate=0.001,
        confidence=1.0,
        source="demo"
    ))
    
    stock.add_force(Force(
        name="中期力示例",
        magnitude=50,
        direction=ForceDirection.BULLISH,
        force_type=ForceType.MID_TERM,
        start_date=start_date,
        decay_rate=0.01,
        confidence=1.0,
        source="demo"
    ))
    
    stock.add_force(Force(
        name="短期力示例",
        magnitude=50,
        direction=ForceDirection.BULLISH,
        force_type=ForceType.SHORT_TERM,
        start_date=start_date,
        decay_rate=0.1,
        confidence=1.0,
        source="demo"
    ))
    
    analyzer = StockForceAnalyzer(stock)
    
    print("\n力的衰减对比（初始值均为50）：")
    print("-" * 60)
    print(f"{'日期':<15} {'长期力':<12} {'中期力':<12} {'短期力':<12}")
    print("-" * 60)
    
    for days in [0, 7, 14, 30, 60, 90, 180, 365]:
        date = start_date + timedelta(days=days)
        forces_by_type = analyzer.calculate_force_by_type(date)
        print(f"Day {days:<10} {forces_by_type[ForceType.LONG_TERM]:<12.2f} "
              f"{forces_by_type[ForceType.MID_TERM]:<12.2f} "
              f"{forces_by_type[ForceType.SHORT_TERM]:<12.2f}")


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║              股票力学量化模型 (Stock Force Model)           ║
    ║                                                          ║
    ║  基于牛顿第二定律: ma = F合                                 ║
    ║  将物理力学原理映射到股票市场分析                            ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # 运行示例
    demo_single_stock_analysis()
    demo_sector_analysis()
    demo_index_analysis()
    demo_force_comparison()
