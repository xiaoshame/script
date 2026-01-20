# -*- coding: utf-8 -*-
"""
新闻事件力量解析器

用于将新闻事件转换为力学模型中的力
支持关键词匹配和事件分类
"""

import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from stock_force_model import Force, ForceDirection, ForceType, ForceFactory


class EventCategory(Enum):
    """事件类别"""
    MONETARY_POLICY = "货币政策"      # 央行政策
    FISCAL_POLICY = "财政政策"        # 财政政策
    INDUSTRY_POLICY = "行业政策"      # 行业政策
    COMPANY_EARNINGS = "公司业绩"     # 财报相关
    MANAGEMENT = "管理层变动"         # 人事变动
    CAPITAL = "资本运作"              # 并购重组等
    LEGAL = "法律风险"                # 法律诉讼
    MARKET = "市场情绪"               # 市场情绪
    INTERNATIONAL = "国际事件"        # 国际事件
    TECHNICAL = "技术突破"            # 技术创新
    PRODUCT = "产品服务"              # 产品服务
    OTHER = "其他"


@dataclass
class NewsEvent:
    """新闻事件"""
    title: str
    content: str
    publish_time: datetime
    source: str
    symbols: List[str] = None  # 相关股票代码
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = []


@dataclass
class ParsedEvent:
    """解析后的事件"""
    event: NewsEvent
    category: EventCategory
    direction: ForceDirection
    magnitude: float
    force_type: ForceType
    confidence: float
    keywords_matched: List[str]


class NewsForceParser:
    """
    新闻力量解析器
    
    将新闻事件解析为力学模型中的力
    """
    
    # 关键词配置
    BULLISH_KEYWORDS = {
        # 货币政策 - 利多
        ForceType.LONG_TERM: {
            "降息": (50, 0.9, EventCategory.MONETARY_POLICY),
            "降准": (45, 0.9, EventCategory.MONETARY_POLICY),
            "宽松": (40, 0.8, EventCategory.MONETARY_POLICY),
            "刺激": (35, 0.7, EventCategory.FISCAL_POLICY),
            "补贴": (30, 0.8, EventCategory.FISCAL_POLICY),
        },
        # 中期利多
        ForceType.MID_TERM: {
            "业绩超预期": (45, 0.85, EventCategory.COMPANY_EARNINGS),
            "净利润增长": (40, 0.8, EventCategory.COMPANY_EARNINGS),
            "营收大增": (35, 0.8, EventCategory.COMPANY_EARNINGS),
            "战略合作": (30, 0.7, EventCategory.CAPITAL),
            "并购": (35, 0.75, EventCategory.CAPITAL),
            "获得订单": (30, 0.75, EventCategory.PRODUCT),
            "技术突破": (35, 0.7, EventCategory.TECHNICAL),
            "产品获批": (40, 0.8, EventCategory.PRODUCT),
            "行业利好": (30, 0.7, EventCategory.INDUSTRY_POLICY),
            "扶持政策": (35, 0.75, EventCategory.INDUSTRY_POLICY),
            "估值修复": (25, 0.65, EventCategory.MARKET),
        },
        # 短期利多
        ForceType.SHORT_TERM: {
            "涨停": (20, 0.6, EventCategory.MARKET),
            "大涨": (15, 0.55, EventCategory.MARKET),
            "资金流入": (25, 0.7, EventCategory.MARKET),
            "北向买入": (30, 0.75, EventCategory.MARKET),
            "机构增持": (25, 0.7, EventCategory.CAPITAL),
            "回购": (30, 0.8, EventCategory.CAPITAL),
            "增持": (25, 0.75, EventCategory.CAPITAL),
            "利好": (20, 0.6, EventCategory.OTHER),
            "突破": (15, 0.5, EventCategory.TECHNICAL),
        }
    }
    
    BEARISH_KEYWORDS = {
        # 货币政策 - 利空
        ForceType.LONG_TERM: {
            "加息": (50, 0.9, EventCategory.MONETARY_POLICY),
            "紧缩": (45, 0.85, EventCategory.MONETARY_POLICY),
            "通胀": (30, 0.7, EventCategory.MONETARY_POLICY),
            "衰退": (40, 0.75, EventCategory.MONETARY_POLICY),
        },
        # 中期利空
        ForceType.MID_TERM: {
            "业绩下滑": (45, 0.85, EventCategory.COMPANY_EARNINGS),
            "亏损": (50, 0.9, EventCategory.COMPANY_EARNINGS),
            "营收下降": (35, 0.8, EventCategory.COMPANY_EARNINGS),
            "诉讼": (30, 0.7, EventCategory.LEGAL),
            "违规": (40, 0.8, EventCategory.LEGAL),
            "处罚": (35, 0.8, EventCategory.LEGAL),
            "被调查": (45, 0.85, EventCategory.LEGAL),
            "行业监管": (30, 0.7, EventCategory.INDUSTRY_POLICY),
            "产能过剩": (25, 0.65, EventCategory.INDUSTRY_POLICY),
            "竞争加剧": (20, 0.6, EventCategory.INDUSTRY_POLICY),
        },
        # 短期利空
        ForceType.SHORT_TERM: {
            "跌停": (25, 0.65, EventCategory.MARKET),
            "大跌": (20, 0.6, EventCategory.MARKET),
            "资金流出": (25, 0.7, EventCategory.MARKET),
            "北向卖出": (30, 0.75, EventCategory.MARKET),
            "减持": (30, 0.8, EventCategory.CAPITAL),
            "高管离职": (25, 0.7, EventCategory.MANAGEMENT),
            "被抓": (50, 0.9, EventCategory.LEGAL),
            "辞职": (20, 0.65, EventCategory.MANAGEMENT),
            "利空": (20, 0.6, EventCategory.OTHER),
            "跳水": (20, 0.6, EventCategory.MARKET),
            "闪崩": (30, 0.7, EventCategory.MARKET),
        }
    }
    
    # 力量调节因子（根据标题中的程度词调整）
    INTENSITY_MODIFIERS = {
        "大幅": 1.5,
        "超": 1.4,
        "暴": 1.6,
        "巨": 1.5,
        "显著": 1.3,
        "略": 0.6,
        "小幅": 0.5,
        "微": 0.4,
        "稍": 0.5,
    }
    
    def __init__(self):
        """初始化解析器"""
        pass
    
    def parse_news(self, event: NewsEvent) -> Optional[ParsedEvent]:
        """
        解析新闻事件
        
        Args:
            event: 新闻事件
            
        Returns:
            解析后的事件，如果无法解析则返回None
        """
        text = event.title + " " + event.content
        
        # 尝试匹配利多关键词
        bullish_result = self._match_keywords(text, self.BULLISH_KEYWORDS)
        
        # 尝试匹配利空关键词
        bearish_result = self._match_keywords(text, self.BEARISH_KEYWORDS)
        
        # 选择匹配度更高的结果
        if bullish_result and bearish_result:
            if bullish_result[0] >= bearish_result[0]:
                magnitude, force_type, category, confidence, keywords = bullish_result
                direction = ForceDirection.BULLISH
            else:
                magnitude, force_type, category, confidence, keywords = bearish_result
                direction = ForceDirection.BEARISH
        elif bullish_result:
            magnitude, force_type, category, confidence, keywords = bullish_result
            direction = ForceDirection.BULLISH
        elif bearish_result:
            magnitude, force_type, category, confidence, keywords = bearish_result
            direction = ForceDirection.BEARISH
        else:
            return None
        
        # 应用程度修饰词
        magnitude = self._apply_intensity_modifiers(text, magnitude)
        
        return ParsedEvent(
            event=event,
            category=category,
            direction=direction,
            magnitude=magnitude,
            force_type=force_type,
            confidence=confidence,
            keywords_matched=keywords
        )
    
    def _match_keywords(self, text: str, 
                       keyword_dict: Dict) -> Optional[Tuple[float, ForceType, EventCategory, float, List[str]]]:
        """
        匹配关键词
        
        Args:
            text: 文本
            keyword_dict: 关键词字典
            
        Returns:
            (magnitude, force_type, category, confidence, keywords) 或 None
        """
        best_match = None
        best_magnitude = 0
        matched_keywords = []
        
        for force_type, keywords in keyword_dict.items():
            for keyword, (magnitude, confidence, category) in keywords.items():
                if keyword in text:
                    matched_keywords.append(keyword)
                    if magnitude > best_magnitude:
                        best_magnitude = magnitude
                        best_match = (magnitude, force_type, category, confidence, [keyword])
        
        if best_match:
            # 更新匹配的关键词列表
            best_match = (best_match[0], best_match[1], best_match[2], 
                         best_match[3], matched_keywords)
        
        return best_match
    
    def _apply_intensity_modifiers(self, text: str, magnitude: float) -> float:
        """
        应用程度修饰词
        
        Args:
            text: 文本
            magnitude: 原始力度
            
        Returns:
            调整后的力度
        """
        modifier = 1.0
        for word, factor in self.INTENSITY_MODIFIERS.items():
            if word in text:
                modifier = max(modifier, factor) if factor > 1 else min(modifier, factor)
        
        return magnitude * modifier
    
    def create_force_from_event(self, parsed: ParsedEvent) -> Force:
        """
        从解析后的事件创建力
        
        Args:
            parsed: 解析后的事件
            
        Returns:
            Force对象
        """
        # 根据力类型确定衰减率
        decay_rates = {
            ForceType.LONG_TERM: 0.001,
            ForceType.MID_TERM: 0.01,
            ForceType.SHORT_TERM: 0.1,
        }
        
        return Force(
            name=f"[{parsed.category.value}] {parsed.event.title[:30]}",
            magnitude=parsed.magnitude,
            direction=parsed.direction,
            force_type=parsed.force_type,
            start_date=parsed.event.publish_time,
            decay_rate=decay_rates[parsed.force_type],
            confidence=parsed.confidence,
            source=f"news:{parsed.event.source}"
        )
    
    def batch_parse(self, events: List[NewsEvent]) -> List[Force]:
        """
        批量解析新闻事件
        
        Args:
            events: 新闻事件列表
            
        Returns:
            Force列表
        """
        forces = []
        for event in events:
            parsed = self.parse_news(event)
            if parsed:
                force = self.create_force_from_event(parsed)
                forces.append(force)
        return forces


class PolicyForceGenerator:
    """
    政策力量生成器
    
    用于生成常见政策事件的力
    """
    
    @staticmethod
    def fed_rate_decision(rate_change: float, date: datetime) -> Force:
        """
        美联储利率决议
        
        Args:
            rate_change: 利率变化（基点），正数为加息，负数为降息
            date: 决议日期
            
        Returns:
            Force对象
        """
        magnitude = min(abs(rate_change) * 2, 60)
        
        if rate_change < 0:
            direction = ForceDirection.BULLISH
            name = f"美联储降息{abs(rate_change)}基点"
        elif rate_change > 0:
            direction = ForceDirection.BEARISH
            name = f"美联储加息{rate_change}基点"
        else:
            direction = ForceDirection.NEUTRAL
            name = "美联储维持利率不变"
            magnitude = 10
        
        return Force(
            name=name,
            magnitude=magnitude,
            direction=direction,
            force_type=ForceType.LONG_TERM,
            start_date=date,
            decay_rate=0.0008,  # 非常缓慢的衰减
            confidence=0.95,
            source="fed_policy"
        )
    
    @staticmethod
    def pboc_rrr_change(change_pct: float, date: datetime) -> Force:
        """
        人民银行存款准备金率变化
        
        Args:
            change_pct: 准备金率变化（百分点），正数为上调，负数为下调
            date: 决议日期
            
        Returns:
            Force对象
        """
        magnitude = min(abs(change_pct) * 100, 50)
        
        if change_pct < 0:
            direction = ForceDirection.BULLISH
            name = f"央行降准{abs(change_pct)}个百分点"
        elif change_pct > 0:
            direction = ForceDirection.BEARISH
            name = f"央行上调准备金率{change_pct}个百分点"
        else:
            return None
        
        return Force(
            name=name,
            magnitude=magnitude,
            direction=direction,
            force_type=ForceType.LONG_TERM,
            start_date=date,
            decay_rate=0.001,
            confidence=0.9,
            source="pboc_policy"
        )
    
    @staticmethod
    def industry_policy(industry: str, policy_name: str,
                       is_supportive: bool, date: datetime,
                       importance: int = 2) -> Force:
        """
        行业政策
        
        Args:
            industry: 行业名称
            policy_name: 政策名称
            is_supportive: 是否为扶持政策
            date: 发布日期
            importance: 重要程度 (1-3)
            
        Returns:
            Force对象
        """
        base_magnitude = importance * 15
        direction = ForceDirection.BULLISH if is_supportive else ForceDirection.BEARISH
        
        return Force(
            name=f"[{industry}] {policy_name}",
            magnitude=base_magnitude,
            direction=direction,
            force_type=ForceType.MID_TERM,
            start_date=date,
            decay_rate=0.005,
            confidence=0.8,
            source="industry_policy"
        )


# 示例使用
def demo_news_parsing():
    """
    新闻解析示例
    """
    print("\n" + "="*60)
    print("新闻力量解析示例")
    print("="*60)
    
    # 创建解析器
    parser = NewsForceParser()
    
    # 模拟新闻事件
    news_events = [
        NewsEvent(
            title="美联储宣布降息25基点，市场反应积极",
            content="美联储在本次议息会议上决定将联邦基金利率下调25个基点...",
            publish_time=datetime(2025, 9, 15),
            source="财经新闻",
            symbols=["000001", "000300"]
        ),
        NewsEvent(
            title="某上市公司董事长被调查，股价跌停",
            content="据消息人士透露，该公司董事长因涉嫌违规被有关部门带走调查...",
            publish_time=datetime(2025, 10, 1),
            source="证券时报",
            symbols=["600001"]
        ),
        NewsEvent(
            title="三季度业绩大幅超预期，净利润同比增长150%",
            content="公司发布三季报，实现营业收入XX亿元，同比增长80%...",
            publish_time=datetime(2025, 10, 28),
            source="公司公告",
            symbols=["000002"]
        ),
        NewsEvent(
            title="北向资金大幅买入，单日净流入超200亿",
            content="今日北向资金表现活跃，沪股通净买入XX亿，深股通净买入XX亿...",
            publish_time=datetime(2025, 11, 5),
            source="财经数据",
            symbols=["000001"]
        ),
        NewsEvent(
            title="行业监管趋严，多家公司收到警示函",
            content="监管部门发文加强行业监管，多家公司因违规被出具警示函...",
            publish_time=datetime(2025, 11, 10),
            source="证监会",
            symbols=["600100", "600101"]
        )
    ]
    
    print("\n【新闻解析结果】\n")
    
    for event in news_events:
        parsed = parser.parse_news(event)
        if parsed:
            direction_str = "利多" if parsed.direction == ForceDirection.BULLISH else "利空"
            print(f"标题: {event.title}")
            print(f"  → 分类: {parsed.category.value}")
            print(f"  → 方向: {direction_str}")
            print(f"  → 力度: {parsed.magnitude:.1f}")
            print(f"  → 类型: {parsed.force_type.value}")
            print(f"  → 置信度: {parsed.confidence:.2f}")
            print(f"  → 匹配关键词: {parsed.keywords_matched}")
            print()
    
    # 批量生成力
    print("\n【批量生成力】")
    forces = parser.batch_parse(news_events)
    for force in forces:
        print(f"  • {force.name}")
        print(f"    力度={force.magnitude:.1f}, 方向={force.direction.name}, "
              f"类型={force.force_type.value}")
        print()
    
    # 政策力量示例
    print("\n【政策力量示例】")
    
    # 美联储降息
    fed_force = PolicyForceGenerator.fed_rate_decision(-25, datetime(2025, 9, 15))
    print(f"  • {fed_force.name}")
    print(f"    力度={fed_force.magnitude:.1f}, 衰减率={fed_force.decay_rate}")
    
    # 央行降准
    pboc_force = PolicyForceGenerator.pboc_rrr_change(-0.5, datetime(2025, 10, 1))
    print(f"  • {pboc_force.name}")
    print(f"    力度={pboc_force.magnitude:.1f}, 衰减率={pboc_force.decay_rate}")
    
    # 行业政策
    industry_force = PolicyForceGenerator.industry_policy(
        "新能源",
        "新能源汽车下乡补贴政策",
        is_supportive=True,
        date=datetime(2025, 8, 1),
        importance=3
    )
    print(f"  • {industry_force.name}")
    print(f"    力度={industry_force.magnitude:.1f}, 衰减率={industry_force.decay_rate}")


if __name__ == "__main__":
    demo_news_parsing()
