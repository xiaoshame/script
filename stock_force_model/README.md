# 股票力学量化模型 (Stock Force Quantitative Model)

基于牛顿第二定律的创新股票分析框架

## 核心理念

将经典力学公式映射到股票市场分析：

```
ma = F合
F合 = F分1 + F分2 + ... + F分N
```

**物理意义 → 金融意义：**

| 物理概念 | 金融映射 | 说明 |
|---------|---------|------|
| m (质量) | 市值 | 股票的"惯性"，市值越大越难推动 |
| a (加速度) | 价格变化速度 | 单位时间内的涨跌幅度 |
| F合 (合力) | 消息面合力 | 所有利多利空因素的矢量和 |
| F分 (分力) | 单个消息/事件 | 可以是利多(正)或利空(负) |

## 力的分类

根据作用时间，将力分为三类：

### 1. 长期力 (Long-term Force)
- **作用时间**: > 1年
- **衰减率**: 0.001 (约693天半衰期)
- **典型案例**:
  - 美联储降息/加息周期
  - 经济周期（复苏/衰退）
  - 行业长期趋势

### 2. 中期力 (Mid-term Force)
- **作用时间**: 1个月 ~ 1年
- **衰减率**: 0.01 (约69天半衰期)
- **典型案例**:
  - 季度财报
  - 行业政策
  - 估值变化

### 3. 短期力 (Short-term Force)
- **作用时间**: < 1个月
- **衰减率**: 0.1 (约7天半衰期)
- **典型案例**:
  - 突发新闻
  - 技术面信号
  - 资金流向

## 项目结构

```
stock_force_model/
├── stock_force_model.py    # 核心模型定义
├── force_indicators.py     # 技术/基本面指标计算
├── news_parser.py          # 新闻事件解析器
├── backtest.py            # 回测框架
├── main.py                # 主入口和示例
└── README.md              # 说明文档
```

## 快速开始

### 安装依赖

```bash
pip install numpy pandas
```

### 基本使用

```python
from datetime import datetime
from stock_force_model import StockEntity, Force, ForceDirection, ForceType, StockForceAnalyzer

# 1. 创建股票实体
stock = StockEntity(
    symbol="600519",
    name="贵州茅台",
    market_cap=20000,  # 2万亿市值
    entity_type="stock"
)

# 2. 添加力
stock.add_force(Force(
    name="美联储降息周期",
    magnitude=50,
    direction=ForceDirection.BULLISH,  # 利多
    force_type=ForceType.LONG_TERM,    # 长期力
    start_date=datetime(2025, 9, 1),
    decay_rate=0.001,
    confidence=0.9,
    source="policy"
))

stock.add_force(Force(
    name="高管减持公告",
    magnitude=20,
    direction=ForceDirection.BEARISH,  # 利空
    force_type=ForceType.SHORT_TERM,   # 短期力
    start_date=datetime(2026, 1, 8),
    decay_rate=0.1,
    confidence=0.8,
    source="news"
))

# 3. 创建分析器
analyzer = StockForceAnalyzer(stock)

# 4. 分析
current_date = datetime(2026, 1, 12)
net_force = analyzer.calculate_net_force(current_date)
acceleration = analyzer.calculate_acceleration(current_date)

print(f"合力: {net_force:.2f}")
print(f"加速度: {acceleration:.4f}")
print(f"预期日涨跌幅: {acceleration:.2f}%")

# 5. 生成报告
report = analyzer.generate_report(current_date)
print(report)
```

### 使用新闻解析器

```python
from news_parser import NewsForceParser, NewsEvent

parser = NewsForceParser()

event = NewsEvent(
    title="公司业绩大幅超预期，净利润增长150%",
    content="...",
    publish_time=datetime(2025, 10, 28),
    source="公司公告"
)

parsed = parser.parse_news(event)
if parsed:
    force = parser.create_force_from_event(parsed)
    stock.add_force(force)
```

### 运行回测

```python
from backtest import Backtester, ForceBasedStrategy
import pandas as pd

# 准备价格数据
prices = pd.DataFrame({
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...]
}, index=pd.date_range(...))

# 创建策略
strategy = ForceBasedStrategy(
    acceleration_buy_threshold=0.3,
    acceleration_sell_threshold=-0.3,
    stop_loss_pct=0.08,
    take_profit_pct=0.15
)

# 运行回测
backtester = Backtester(prices, stock, strategy, initial_capital=100000)
result = backtester.run(start_date, end_date)
backtester.print_report(result)
```

## 运行示例

```bash
# 运行主示例
python main.py

# 运行回测示例
python backtest.py

# 运行新闻解析示例
python news_parser.py
```

## 核心类说明

### Force (力)
```python
@dataclass
class Force:
    name: str              # 力的名称
    magnitude: float       # 力的大小 (0-100)
    direction: ForceDirection  # 方向 (BULLISH/BEARISH/NEUTRAL)
    force_type: ForceType  # 类型 (LONG_TERM/MID_TERM/SHORT_TERM)
    start_date: datetime   # 开始作用时间
    decay_rate: float      # 衰减率
    confidence: float      # 置信度 (0-1)
    source: str           # 来源
```

### StockEntity (股票实体)
```python
@dataclass
class StockEntity:
    symbol: str           # 代码
    name: str            # 名称
    market_cap: float    # 市值（亿元）
    entity_type: str     # 类型 (stock/sector/index)
    forces: List[Force]  # 作用力列表
```

### StockForceAnalyzer (分析器)
- `calculate_net_force()`: 计算合力
- `calculate_acceleration()`: 计算加速度
- `get_force_decomposition()`: 力的正交分解
- `predict_trend()`: 趋势预测
- `generate_report()`: 生成分析报告

## 投资建议（基于模型）

| 场景 | 关注重点 | 建议 |
|------|---------|------|
| 短期交易 | 短期力变化 | 关注技术信号和突发新闻 |
| 中期投资 | 中期力 + 长期力 | 关注财报和行业政策 |
| 长期投资 | 长期力方向 | 关注宏观经济和央行政策 |

## 模型优势

1. **直观的物理类比**: 将复杂的市场分析简化为力学问题
2. **多维度分析**: 综合考虑技术面、基本面、消息面
3. **时间衰减**: 自动考虑消息的时效性
4. **可扩展性**: 易于添加新的力量来源
5. **量化输出**: 提供可交易的具体信号

## 局限性

1. 力的大小和衰减率需要主观设定
2. 市场情绪难以精确量化
3. 黑天鹅事件难以预测
4. 历史回测不代表未来表现

## 风险提示

⚠️ **本模型仅供学习研究使用，不构成投资建议。股市有风险，投资需谨慎。**

## License

MIT License
