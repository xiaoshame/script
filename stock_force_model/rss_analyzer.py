# -*- coding: utf-8 -*-
"""
RSS新闻源解析模块

自动获取财经新闻RSS，使用大模型分析新闻是否可以作为力的因子
支持:
- 财联社热点
- 其他RSS源
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json
import re
import time
import os
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class RSSItem:
    """RSS条目"""
    title: str
    description: str
    link: str
    pub_date: datetime
    source: str
    guid: str = ""
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "link": self.link,
            "pub_date": self.pub_date.isoformat(),
            "source": self.source,
            "guid": self.guid
        }


@dataclass
class ForceAnalysisResult:
    """大模型分析结果"""
    is_force: bool              # 是否可以作为力
    direction: str              # bullish/bearish/neutral
    magnitude: float            # 力度 0-100
    force_type: str             # long_term/mid_term/short_term
    confidence: float           # 置信度 0-1
    affected_symbols: List[str] # 影响的股票代码
    affected_sectors: List[str] # 影响的行业
    reason: str                 # 分析理由
    keywords: List[str]         # 关键词
    
    def to_dict(self) -> dict:
        return {
            "is_force": self.is_force,
            "direction": self.direction,
            "magnitude": self.magnitude,
            "force_type": self.force_type,
            "confidence": self.confidence,
            "affected_symbols": self.affected_symbols,
            "affected_sectors": self.affected_sectors,
            "reason": self.reason,
            "keywords": self.keywords
        }


class RSSFetcher:
    """
    RSS源获取器
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_rss(self, url: str, timeout: int = 10) -> List[RSSItem]:
        """
        获取RSS源（支持RSS和Atom格式）
        
        Args:
            url: RSS URL
            timeout: 超时时间
            
        Returns:
            RSSItem列表
        """
        try:
            response = self.session.get(url, timeout=timeout)
            response.encoding = 'utf-8'
            
            # 解析XML
            root = ET.fromstring(response.content)
            
            items = []
            
            # 检测是Atom还是RSS格式
            # Atom格式的根标签通常是 <feed>，包含 <entry>
            # RSS格式的根标签通常是 <rss>，包含 <item>
            
            # 尝试Atom格式 (namespace处理)
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom'
            }
            
            # 先尝试带命名空间的Atom
            atom_entries = root.findall('.//atom:entry', namespaces)
            if not atom_entries:
                # 尝试不带命名空间的Atom
                atom_entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')
            if not atom_entries:
                # 尝试直接查找entry
                atom_entries = root.findall('.//entry')
            
            if atom_entries:
                # Atom格式
                for entry in atom_entries:
                    # 处理命名空间
                    ns = '{http://www.w3.org/2005/Atom}'
                    
                    # 注意：不能使用 or 操作符，因为 XML 元素的真值测试已被弃用
                    title = entry.find(f'{ns}title')
                    if title is None:
                        title = entry.find('title')
                    
                    summary = entry.find(f'{ns}summary')
                    if summary is None:
                        summary = entry.find('summary')
                    
                    content = entry.find(f'{ns}content')
                    if content is None:
                        content = entry.find('content')
                    
                    link = entry.find(f'{ns}link')
                    if link is None:
                        link = entry.find('link')
                    
                    published = entry.find(f'{ns}published')
                    if published is None:
                        published = entry.find('published')
                    
                    updated = entry.find(f'{ns}updated')
                    if updated is None:
                        updated = entry.find('updated')
                    
                    id_elem = entry.find(f'{ns}id')
                    if id_elem is None:
                        id_elem = entry.find('id')
                    
                    # 获取链接（Atom的link是属性）
                    link_url = ""
                    if link is not None:
                        link_url = link.get('href', '') or link.text or ""
                    
                    # 获取描述（优先summary，其次content）
                    desc_text = ""
                    if summary is not None and summary.text:
                        desc_text = summary.text
                    elif content is not None and content.text:
                        desc_text = content.text
                    
                    # 获取日期（优先published，其次updated）
                    date_str = ""
                    if published is not None and published.text:
                        date_str = published.text
                    elif updated is not None and updated.text:
                        date_str = updated.text
                    
                    try:
                        parsed_date = self._parse_date(date_str)
                    except:
                        parsed_date = datetime.now()
                    
                    items.append(RSSItem(
                        title=title.text if title is not None and title.text else "",
                        description=self._clean_html(desc_text),
                        link=link_url,
                        pub_date=parsed_date,
                        source=url,
                        guid=id_elem.text if id_elem is not None and id_elem.text else ""
                    ))
            else:
                # 标准RSS格式
                for item in root.findall('.//item'):
                    title = item.find('title')
                    description = item.find('description')
                    link = item.find('link')
                    pub_date = item.find('pubDate')
                    guid = item.find('guid')
                    
                    # 解析日期
                    date_str = pub_date.text if pub_date is not None else ""
                    try:
                        parsed_date = self._parse_date(date_str)
                    except:
                        parsed_date = datetime.now()
                    
                    items.append(RSSItem(
                        title=title.text if title is not None else "",
                        description=self._clean_html(description.text) if description is not None else "",
                        link=link.text if link is not None else "",
                        pub_date=parsed_date,
                        source=url,
                        guid=guid.text if guid is not None else ""
                    ))
            
            return items
            
        except Exception as e:
            print(f"[fetch_rss] Error fetching {url}: {e}")
            return []
    
    def _parse_date(self, date_str: str) -> datetime:
        """解析日期字符串"""
        if not date_str:
            return datetime.now()
        
        # 常见的RSS日期格式
        formats = [
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S GMT",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except:
                continue
        
        return datetime.now()
    
    def _clean_html(self, text: str) -> str:
        """清理HTML标签"""
        if not text:
            return ""
        # 移除HTML标签
        clean = re.sub(r'<[^>]+>', '', text)
        # 移除多余空白
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean
    
    def fetch_cls_hot(self) -> List[RSSItem]:
        """
        获取财联社热点新闻
        
        Returns:
            RSSItem列表
        """
        url = "https://rsshub.rss.zgdnz.cc/cls/hot"
        return self.fetch_rss(url)
    
    def fetch_cls_depth(self) -> List[RSSItem]:
        """获取财联社深度文章"""
        url = "https://rsshub.rss.zgdnz.cc/cls/depth/1000"
        return self.fetch_rss(url)
    
    def fetch_jin10(self) -> List[RSSItem]:
        """获取金十数据"""
        url = "https://rsshub.rss.zgdnz.cc/jin10"
        return self.fetch_rss(url)


class LLMAnalyzer(ABC):
    """
    大模型分析器基类
    """
    
    @abstractmethod
    def analyze(self, news: RSSItem) -> Optional[ForceAnalysisResult]:
        """分析新闻是否可以作为力"""
        pass
    
    @abstractmethod
    def batch_analyze(self, news_list: List[RSSItem]) -> List[ForceAnalysisResult]:
        """批量分析"""
        pass


class GeminiAnalyzer(LLMAnalyzer):
    """
    使用Google Gemini API分析新闻（基于 google-genai SDK）
    """
    
    ANALYSIS_PROMPT = """你是一个专业的金融分析师，需要分析以下新闻是否会对股票市场产生影响。

新闻标题: {title}
新闻内容: {description}
发布时间: {pub_date}

请分析这条新闻是否可以作为影响股票价格的"力"，并按以下JSON格式返回结果：

{{
    "is_force": true,
    "direction": "bullish",
    "magnitude": 50,
    "force_type": "short_term",
    "confidence": 0.7,
    "affected_symbols": ["600519"],
    "affected_sectors": ["白酒"],
    "reason": "判断理由",
    "keywords": ["关键词"]
}}

字段说明:
- is_force: 是否会对市场产生影响 (true/false)
- direction: 利多"bullish"/利空"bearish"/中性"neutral"
- magnitude: 影响力度 0-100
- force_type: 长期力"long_term"(>1年)/中期力"mid_term"(1个月-1年)/短期力"short_term"(<1个月)
- confidence: 置信度 0-1
- affected_symbols: 可能受影响的股票代码
- affected_sectors: 可能受影响的行业
- reason: 简短说明判断理由
- keywords: 关键词

判断标准:
1. 长期力: 央行政策(降息/加息)、重大经济政策、行业长期趋势
2. 中期力: 季度财报、行业政策、公司重大事件(并购/重组)
3. 短期力: 突发新闻、技术面信号、资金流向、日常公告

力度判断:
- 90-100: 重大事件(如央行降息、公司造假)
- 70-89: 较大事件(如财报大幅超/低预期)
- 40-69: 中等事件(如行业政策、资金流向)
- 20-39: 小事件(如日常公告)
- 0-19: 无实质影响

只返回JSON，不要其他内容。"""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = "gemini-3-flash-preview"):
        """
        初始化
        
        Args:
            api_key: Gemini API Key，如果不传则从环境变量获取
            base_url: API基础URL (可选，用于自定义代理)
            model: 使用的模型，默认 gemini-3-pro-preview
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.client = None
        
        print(f"[GeminiAnalyzer] 使用模型: {model}, 基础URL: {self.base_url}")
        
        if not self.api_key:
            print("[警告] 未设置GEMINI_API_KEY，大模型分析功能将不可用")
        else:
            self._init_client()
    
    def _init_client(self):
        """初始化 Gemini 客户端"""
        try:
            from google import genai
            from google.genai import types
            
            self.client = genai.Client(
                vertexai=True,
                api_key=self.api_key,
                http_options=types.HttpOptions(
                    base_url=self.base_url
                )
            )
            self.types = types
        except ImportError:
            print("[警告] 未安装 google-genai 包，请运行: pip install google-genai")
            self.client = None
        except Exception as e:
            print(f"[警告] 初始化 Gemini 客户端失败: {e}")
            self.client = None
    
    def analyze(self, news: RSSItem) -> Optional[ForceAnalysisResult]:
        """
        分析单条新闻
        
        Args:
            news: RSS条目
            
        Returns:
            分析结果或None
        """
        if not self.client:
            return None
        
        try:
            prompt = self.ANALYSIS_PROMPT.format(
                title=news.title,
                description=news.description[:500] if news.description else "",
                pub_date=news.pub_date.strftime("%Y-%m-%d %H:%M")
            )
            
            # 构建消息内容
            msg_text = self.types.Part.from_text(text=prompt)
            contents = [
                self.types.Content(
                    role="user",
                    parts=[msg_text]
                ),
            ]
            
            # 配置生成参数（不使用思考模式，简化输出）
            generate_content_config = self.types.GenerateContentConfig(
                temperature=0.3,
                top_p=0.95,
                max_output_tokens=8192,  # 增加输出限制
                safety_settings=[
                    self.types.SafetySetting(
                        category="HARM_CATEGORY_HATE_SPEECH",
                        threshold="OFF"
                    ),
                    self.types.SafetySetting(
                        category="HARM_CATEGORY_DANGEROUS_CONTENT",
                        threshold="OFF"
                    ),
                    self.types.SafetySetting(
                        category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        threshold="OFF"
                    ),
                    self.types.SafetySetting(
                        category="HARM_CATEGORY_HARASSMENT",
                        threshold="OFF"
                    ),
                ],
            )
            
            # 使用非流式 API 生成内容
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            )
            
            # 提取文本内容
            content = None
            if hasattr(response, 'text') and response.text:
                content = response.text
            elif hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content and hasattr(candidate.content, 'parts') and candidate.content.parts:
                    text_parts = []
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                    content = ''.join(text_parts) if text_parts else None
            
            if not content:
                print("[Gemini] 未能获取响应内容")
                return None
            
            # 解析JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
                
                return ForceAnalysisResult(
                    is_force=data.get('is_force', False),
                    direction=data.get('direction', 'neutral'),
                    magnitude=float(data.get('magnitude', 0)),
                    force_type=data.get('force_type', 'short_term'),
                    confidence=float(data.get('confidence', 0.5)),
                    affected_symbols=data.get('affected_symbols', []),
                    affected_sectors=data.get('affected_sectors', []),
                    reason=data.get('reason', ''),
                    keywords=data.get('keywords', [])
                )
            
            return None
            
        except Exception as e:
            print(f"[Gemini] Error analyzing: {e}")
            return None
    
    def batch_analyze(self, news_list: List[RSSItem]) -> List[ForceAnalysisResult]:
        """
        批量分析新闻
        
        Args:
            news_list: RSS条目列表
            
        Returns:
            分析结果列表
        """
        results = []
        for news in news_list:
            result = self.analyze(news)
            if result:
                results.append(result)
            # 避免API限流
            time.sleep(0.5)
        return results


# 保留别名以兼容旧代码
OpenAIAnalyzer = GeminiAnalyzer


class LocalRuleAnalyzer(LLMAnalyzer):
    """
    本地规则分析器
    
    不依赖大模型，使用关键词规则分析
    适合没有API Key的情况
    """
    
    # 关键词规则配置
    RULES = {
        # 长期力 - 利多
        "long_term_bullish": {
            "keywords": ["降息", "降准", "宽松", "刺激政策", "经济复苏", "GDP增长"],
            "magnitude": 50,
            "confidence": 0.8
        },
        # 长期力 - 利空
        "long_term_bearish": {
            "keywords": ["加息", "紧缩", "通胀", "经济衰退", "GDP下滑"],
            "magnitude": 50,
            "confidence": 0.8
        },
        # 中期力 - 利多
        "mid_term_bullish": {
            "keywords": ["业绩超预期", "净利润增长", "营收大增", "订单", "并购", 
                        "战略合作", "获批", "扶持政策", "补贴"],
            "magnitude": 35,
            "confidence": 0.7
        },
        # 中期力 - 利空
        "mid_term_bearish": {
            "keywords": ["业绩下滑", "亏损", "营收下降", "诉讼", "违规", 
                        "处罚", "被调查", "监管", "产能过剩"],
            "magnitude": 35,
            "confidence": 0.7
        },
        # 短期力 - 利多
        "short_term_bullish": {
            "keywords": ["涨停", "大涨", "资金流入", "北向买入", "增持", 
                        "回购", "机构加仓", "利好"],
            "magnitude": 25,
            "confidence": 0.6
        },
        # 短期力 - 利空
        "short_term_bearish": {
            "keywords": ["跌停", "大跌", "资金流出", "北向卖出", "减持", 
                        "高管离职", "被抓", "利空", "闪崩"],
            "magnitude": 25,
            "confidence": 0.6
        }
    }
    
    # 行业关键词映射
    SECTOR_KEYWORDS = {
        "白酒": ["茅台", "五粮液", "泸州老窖", "洋河", "白酒", "酒业"],
        "新能源汽车": ["新能源", "电动车", "锂电", "特斯拉", "比亚迪", "宁德时代"],
        "半导体": ["芯片", "半导体", "晶圆", "光刻", "集成电路"],
        "医药": ["医药", "药品", "创新药", "医疗", "疫苗", "生物医药"],
        "银行": ["银行", "信贷", "存款", "贷款", "金融"],
        "房地产": ["房地产", "楼市", "房价", "地产", "开发商"],
        "互联网": ["互联网", "科技", "电商", "平台", "数字经济"],
        "消费": ["消费", "零售", "电商", "品牌", "快消"],
    }
    
    # 程度词
    INTENSITY_WORDS = {
        "大幅": 1.5, "暴": 1.6, "巨": 1.5, "超": 1.4, 
        "显著": 1.3, "重大": 1.4, "历史": 1.5,
        "略": 0.6, "小幅": 0.5, "微": 0.4, "稍": 0.5
    }
    
    def analyze(self, news: RSSItem) -> Optional[ForceAnalysisResult]:
        """
        使用规则分析新闻
        
        Args:
            news: RSS条目
            
        Returns:
            分析结果或None
        """
        text = news.title + " " + (news.description or "")
        
        # 匹配规则
        matched_rule = None
        matched_keywords = []
        
        for rule_name, rule in self.RULES.items():
            for keyword in rule['keywords']:
                if keyword in text:
                    matched_keywords.append(keyword)
                    if matched_rule is None:
                        matched_rule = (rule_name, rule)
        
        if not matched_rule:
            return ForceAnalysisResult(
                is_force=False,
                direction="neutral",
                magnitude=0,
                force_type="short_term",
                confidence=0.3,
                affected_symbols=[],
                affected_sectors=[],
                reason="未匹配到任何关键词规则",
                keywords=[]
            )
        
        rule_name, rule = matched_rule
        
        # 解析规则名称
        parts = rule_name.split('_')
        force_type = '_'.join(parts[:2])  # long_term, mid_term, short_term
        direction = parts[-1]  # bullish, bearish
        
        # 计算力度
        magnitude = rule['magnitude']
        
        # 应用程度词调整
        for word, factor in self.INTENSITY_WORDS.items():
            if word in text:
                magnitude *= factor
                break
        
        magnitude = min(magnitude, 100)
        
        # 识别影响的行业
        affected_sectors = []
        for sector, keywords in self.SECTOR_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    affected_sectors.append(sector)
                    break
        
        return ForceAnalysisResult(
            is_force=True,
            direction=direction,
            magnitude=magnitude,
            force_type=force_type,
            confidence=rule['confidence'],
            affected_symbols=[],  # 规则模式难以识别具体股票
            affected_sectors=list(set(affected_sectors)),
            reason=f"匹配关键词: {', '.join(matched_keywords[:5])}",
            keywords=matched_keywords
        )
    
    def batch_analyze(self, news_list: List[RSSItem]) -> List[ForceAnalysisResult]:
        """批量分析"""
        return [self.analyze(news) for news in news_list if self.analyze(news)]


class NewsForceIntegrator:
    """
    新闻力量整合器
    
    整合RSS获取和大模型分析，生成可用于力学模型的Force对象
    支持:
    - 多RSS源配置
    - SQLite持久化存储
    - 增量分析
    """
    
    def __init__(self, use_llm: bool = False, 
                 api_key: str = None, 
                 base_url: str = None,
                 model: str = "gemini-2.0-flash",
                 config_path: str = None,
                 db_path: str = None):
        """
        初始化
        
        Args:
            use_llm: 是否使用大模型分析
            api_key: Gemini API Key
            base_url: API基础URL
            model: 使用的模型
            config_path: 配置文件路径
            db_path: 数据库路径
        """
        from rss_database import RSSDatabase, ConfigManager
        
        # 加载配置
        self.config = ConfigManager(config_path or "config.json")
        
        # 初始化数据库
        db_config = self.config.get_database_config()
        self.db = RSSDatabase(db_path or db_config.get('path', 'rss_news.db'))
        
        # RSS获取器
        self.rss_fetcher = RSSFetcher()
        
        # 初始化分析器
        llm_config = self.config.get_llm_config()
        use_llm = use_llm or llm_config.get('use_llm', False)
        
        if use_llm:
            env_key = llm_config.get('api_key_env', 'GEMINI_API_KEY')
            api_key = api_key or os.environ.get(env_key, '')
            if api_key:
                self.analyzer = GeminiAnalyzer(
                    api_key=api_key, 
                    base_url=base_url,
                    model=model or llm_config.get('model', 'gemini-2.0-flash')
                )
                print("[NewsForceIntegrator] 使用Gemini大模型分析器")
            else:
                print(f"[NewsForceIntegrator] 未设置{env_key}，使用本地规则分析器")
                self.analyzer = LocalRuleAnalyzer()
        else:
            print("[NewsForceIntegrator] 使用本地规则分析器")
            self.analyzer = LocalRuleAnalyzer()
        
        # 已处理的新闻缓存（避免重复）
        self._processed_guids = set()
        
        # 从数据库加载已分析的guid到缓存
        self._load_analyzed_guids()
        
        # 分析配置
        self.analysis_config = self.config.get_analysis_config()
    
    def _load_analyzed_guids(self):
        """从数据库加载已分析的新闻guid到缓存"""
        try:
            analyzed = self.db.get_analyzed_guids()
            self._processed_guids.update(analyzed)
            print(f"[NewsForceIntegrator] 已加载 {len(analyzed)} 条已分析新闻缓存")
        except Exception as e:
            print(f"[NewsForceIntegrator] 加载缓存失败: {e}")
    
    def _generate_stable_guid(self, item: RSSItem) -> str:
        """
        生成稳定的guid
        
        只使用标题生成hash，确保同一条新闻不管来自哪个源、什么时间都会被识别为同一条
        这样可以避免重复新闻进入数据库
        """
        import hashlib
        # 只使用标题，去除首尾空白，确保一致性
        content = item.title.strip()
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def fetch_all_sources(self) -> Tuple[int, int]:
        """
        从所有启用的RSS源获取新闻并存入数据库
        
        Returns:
            (总获取记录数, 实际新增条数)
        """
        sources = self.config.get_enabled_sources()
        
        if not sources:
            print("[NewsForceIntegrator] 没有启用的RSS源")
            return 0, 0
        
        print(f"[NewsForceIntegrator] 开始获取 {len(sources)} 个RSS源...")
        
        total_fetched = 0
        total_new = 0
        max_items = self.analysis_config.get('max_items_per_source', 100)
        
        # 收集所有源的新闻，用于跨源重复检测
        all_news_by_title = {}  # title -> [(source_name, news), ...]
        all_news_lists = []  # [(source_name, news_list), ...]
        
        # 第一阶段：获取所有源的新闻
        for source in sources:
            name = source['name']
            url = source['url']
            
            print(f"  - 获取 [{name}]...")
            
            try:
                items = self.rss_fetcher.fetch_rss(url)
                
                if not items:
                    print(f"    [X] 未获取到内容")
                    continue
                
                # 限额处理
                raw_count = len(items)
                process_items = items[:max_items]
                
                # 转换为数据库格式
                news_list = []
                for item in process_items:
                    stable_guid = self._generate_stable_guid(item)
                    news_data = {
                        'guid': stable_guid,
                        'title': item.title,
                        'description': item.description,
                        'link': item.link,
                        'pub_date': item.pub_date.isoformat() if item.pub_date else '',
                        'source_name': name,
                        'source_url': url
                    }
                    news_list.append(news_data)
                    
                    # 记录标题到源的映射（用于跨源重复检测）
                    title_key = item.title.strip()
                    if title_key not in all_news_by_title:
                        all_news_by_title[title_key] = []
                    all_news_by_title[title_key].append((name, news_data))
                
                all_news_lists.append((name, news_list, raw_count))
                print(f"    [OK] 获取 {raw_count} 条, 处理 {len(news_list)} 条")
                
            except Exception as e:
                print(f"    [X] 获取失败: {e}")
        
        # 检测跨源重复
        cross_source_duplicates = {title: sources for title, sources in all_news_by_title.items() if len(sources) > 1}
        
        if cross_source_duplicates:
            print(f"\n  【跨源重复检测】发现 {len(cross_source_duplicates)} 条新闻在多个源中出现:")
            for title, source_list in list(cross_source_duplicates.items())[:10]:
                source_names = [s[0] for s in source_list]
                print(f"    [{' + '.join(source_names)}] {title[:50]}...")
            if len(cross_source_duplicates) > 10:
                print(f"    ... 还有 {len(cross_source_duplicates) - 10} 条跨源重复")
        
        # 第二阶段：存入数据库
        print(f"\n  【存入数据库】")
        for name, news_list, raw_count in all_news_lists:
            added, skipped, _ = self.db.add_news(news_list)
            total_fetched += len(news_list)
            total_new += added
            print(f"    [{name}] 新增 {added} 条, 已存在 {skipped} 条")
        
        # 获取数据库当前总量
        db_stats = self.db.get_statistics()
        total_skipped = total_fetched - total_new
        print(f"[NewsForceIntegrator] 汇总: 处理 {total_fetched} 条, 新增 {total_new} 条, 重复 {total_skipped} 条")
        print(f"[NewsForceIntegrator] 数据库总量: {db_stats['total_news']} 条 (已分析 {db_stats['analyzed_news']}, 待分析 {db_stats['unanalyzed_news']})")
        return total_fetched, total_new
    
    def analyze_pending_news(self, limit: int = None) -> List[Tuple[int, ForceAnalysisResult]]:
        """
        分析数据库中未处理的新闻（并发处理）
        
        Args:
            limit: 最大分析条数
            
        Returns:
            [(news_id, ForceAnalysisResult), ...] 列表
        """
        from rss_database import NewsRecord
        
        batch_size = limit or self.analysis_config.get('batch_size', 10)
        delay = self.analysis_config.get('request_delay', 0.5)
        max_workers = self.analysis_config.get('max_concurrent_requests', 2)
        
        unanalyzed = self.db.get_unanalyzed_news(limit=batch_size)
        
        if not unanalyzed:
            print("[NewsForceIntegrator] 没有待分析的新闻")
            return []
        
        # 过滤掉已在缓存中的新闻（可能已通过其他方法分析）
        truly_unanalyzed = []
        for news in unanalyzed:
            if news.guid not in self._processed_guids:
                truly_unanalyzed.append(news)
            else:
                # 已在缓存中，直接标记为已分析（使用缓存的结果）
                existing = self.db.get_news_by_guid(news.guid)
                if existing and not existing.analyzed:
                    # 从缓存中找不到分析结果，可能是内存缓存，跳过
                    pass
        
        if not truly_unanalyzed:
            print("[NewsForceIntegrator] 所有新闻已在缓存中，无需重新分析")
            return []
        
        print(f"[NewsForceIntegrator] 使用 {max_workers} 个并发线程分析 {len(truly_unanalyzed)} 条新闻（跳过 {len(unanalyzed) - len(truly_unanalyzed)} 条已缓存）...")
        unanalyzed = truly_unanalyzed
        
        results = []
        updates = []
        
        # 创建分析任务列表
        def analyze_news_item(news: NewsRecord) -> Tuple[int, NewsRecord, Optional[ForceAnalysisResult]]:
            """分析单条新闻"""
            try:
                # 转换为RSSItem格式以供分析器使用
                rss_item = RSSItem(
                    title=news.title,
                    description=news.description,
                    link=news.link,
                    pub_date=datetime.fromisoformat(news.pub_date) if news.pub_date else datetime.now(),
                    source=news.source_name,
                    guid=news.guid
                )
                
                # 分析
                analysis = self.analyzer.analyze(rss_item)
                return (news.id, news, analysis)
            except Exception as e:
                print(f"  [X] 分析异常 {news.title[:35]}...: {e}")
                return (news.id, news, None)
        
        # 使用并发线程池进行分析
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            futures = [executor.submit(analyze_news_item, news) for news in unanalyzed]
            
            # 处理完成的任务
            completed = 0
            for future in as_completed(futures):
                news_id, news, analysis = future.result()
                completed += 1
                
                if analysis:
                    analysis_dict = analysis.to_dict()
                    updates.append((news_id, analysis_dict))
                    results.append((news_id, analysis))
                    # 添加到已处理缓存
                    self._processed_guids.add(news.guid)
                    
                    if analysis.is_force:
                        print(f"  [OK] [{analysis.direction}] {news.title[:35]}... "
                              f"(力度:{analysis.magnitude:.0f}) [{completed}/{len(unanalyzed)}]")
                else:
                    # 分析失败，标记为已处理但不是力
                    updates.append((news_id, {
                        'is_force': False,
                        'direction': 'neutral',
                        'magnitude': 0,
                        'force_type': '',
                        'confidence': 0
                    }))
                    # 也添加到缓存，避免重复分析失败的新闻
                    self._processed_guids.add(news.guid)
                
                # 可选延迟
                if delay > 0 and isinstance(self.analyzer, GeminiAnalyzer):
                    time.sleep(delay / max_workers)  # 分散延迟
        
        # 批量更新数据库
        if updates:
            self.db.batch_update_analysis(updates)
            print(f"[NewsForceIntegrator] 更新了 {len(updates)} 条分析结果")
        
        return results
    
    def run_incremental_analysis(self) -> Dict:
        """
        运行增量分析流程
        
        1. 获取所有RSS源的新闻
        2. 分析新增的新闻
        3. 返回统计结果
        
        Returns:
            运行结果统计
        """
        import time as time_module
        start_time = time_module.time()
        
        print("\n" + "=" * 60)
        print("运行增量RSS分析")
        print("=" * 60)
        
        try:
            # 1. 获取所有源
            sources = self.config.get_enabled_sources()
            fetched, new_count = self.fetch_all_sources()
            
            # 2. 分析待处理新闻
            results = self.analyze_pending_news()
            
            # 统计力的数量
            forces_count = sum(1 for _, r in results if r.is_force)
            
            duration = time_module.time() - start_time
            
            # 记录日志
            self.db.log_run(
                sources_count=len(sources),
                news_fetched=fetched,
                news_new=new_count,
                news_analyzed=len(results),
                forces_generated=forces_count,
                duration=duration,
                status="success"
            )
            
            stats = {
                'sources_count': len(sources),
                'news_fetched': fetched,
                'news_new': new_count,
                'news_analyzed': len(results),
                'forces_generated': forces_count,
                'duration': duration
            }
            
            print(f"\n【运行结果】")
            print(f"  RSS源数量: {stats['sources_count']}")
            print(f"  获取新闻: {stats['news_fetched']}")
            print(f"  新增新闻: {stats['news_new']}")
            print(f"  分析新闻: {stats['news_analyzed']}")
            print(f"  生成力量: {stats['forces_generated']}")
            print(f"  耗时: {stats['duration']:.2f}秒")
            
            return stats
            
        except Exception as e:
            duration = time_module.time() - start_time
            self.db.log_run(
                sources_count=len(self.config.get_enabled_sources()),
                duration=duration,
                status="error",
                error=str(e)
            )
            print(f"[NewsForceIntegrator] 运行失败: {e}")
            raise
    
    def get_recent_forces(self, hours: int = 24, limit: int = 50) -> List[Tuple[RSSItem, ForceAnalysisResult]]:
        """
        获取最近的力量新闻
        
        Args:
            hours: 最近多少小时
            limit: 最大返回数量
            
        Returns:
            (RSSItem, ForceAnalysisResult) 列表
        """
        since = datetime.now() - timedelta(hours=hours)
        records = self.db.get_force_news(since=since, limit=limit)
        
        results = []
        for record in records:
            rss_item = RSSItem(
                title=record.title,
                description=record.description,
                link=record.link,
                pub_date=datetime.fromisoformat(record.pub_date) if record.pub_date else datetime.now(),
                source=record.source_name,
                guid=record.guid
            )
            
            # 从存储的JSON恢复分析结果
            if record.analysis_result:
                try:
                    data = json.loads(record.analysis_result)
                    analysis = ForceAnalysisResult(
                        is_force=data.get('is_force', True),
                        direction=data.get('direction', record.direction),
                        magnitude=data.get('magnitude', record.magnitude),
                        force_type=data.get('force_type', record.force_type),
                        confidence=data.get('confidence', record.confidence),
                        affected_symbols=data.get('affected_symbols', []),
                        affected_sectors=data.get('affected_sectors', []),
                        reason=data.get('reason', ''),
                        keywords=data.get('keywords', [])
                    )
                except:
                    analysis = ForceAnalysisResult(
                        is_force=True,
                        direction=record.direction,
                        magnitude=record.magnitude,
                        force_type=record.force_type,
                        confidence=record.confidence,
                        affected_symbols=[],
                        affected_sectors=[],
                        reason='',
                        keywords=[]
                    )
            else:
                analysis = ForceAnalysisResult(
                    is_force=True,
                    direction=record.direction,
                    magnitude=record.magnitude,
                    force_type=record.force_type,
                    confidence=record.confidence,
                    affected_symbols=[],
                    affected_sectors=[],
                    reason='',
                    keywords=[]
                )
            
            results.append((rss_item, analysis))
        
        return results
    
    def get_statistics(self) -> Dict:
        """获取数据库统计信息"""
        return self.db.get_statistics()
    
    def cleanup(self, days: int = None):
        """清理旧数据"""
        db_config = self.config.get_database_config()
        days = days or db_config.get('max_age_days', 30)
        self.db.cleanup_old_news(days)
    
    def fetch_and_analyze_cls(self, max_items: int = 20) -> List[Tuple[RSSItem, ForceAnalysisResult]]:
        """
        获取并分析财联社热点新闻
        
        优化：先查数据库，已分析的新闻直接返回存储结果，不重复调用大模型
        
        Args:
            max_items: 最大获取条数
            
        Returns:
            (新闻, 分析结果) 元组列表
        """
        print("[NewsForceIntegrator] 获取财联社热点新闻...")
        
        news_items = self.rss_fetcher.fetch_cls_hot()
        
        if not news_items:
            print("[NewsForceIntegrator] 未获取到新闻")
            return []
        
        print(f"[NewsForceIntegrator] 获取到 {len(news_items)} 条新闻")
        
        results = []
        new_items = []
        
        # 先检查数据库，找出已分析和未分析的新闻
        for item in news_items[:max_items]:
            # 使用稳定的guid（与fetch_all_sources一致）
            stable_guid = self._generate_stable_guid(item)
            existing = self.db.get_news_by_guid(stable_guid)
            
            if existing and existing.analyzed:
                # 已分析过，直接从数据库恢复结果
                if existing.is_force:
                    analysis = self._restore_analysis_from_record(existing)
                    results.append((item, analysis))
                    print(f"  [OK] [已缓存] {item.title[:35]}...")
            elif stable_guid not in self._processed_guids:
                # 未分析过，加入待分析列表
                item.guid = stable_guid  # 更新为稳定的guid
                new_items.append(item)
                self._processed_guids.add(stable_guid)
        
        if not new_items:
            if results:
                print(f"[NewsForceIntegrator] 从缓存返回 {len(results)} 条已分析新闻")
            else:
                print("[NewsForceIntegrator] 没有新的新闻需要分析")
            return results
        
        print(f"[NewsForceIntegrator] 需要新分析 {len(new_items)} 条新闻...")
        
        # 分析新新闻
        for item in new_items:
            analysis = self.analyzer.analyze(item)
            if analysis:
                # 存储到数据库
                self._save_analysis_to_db(item, analysis)
                
                if analysis.is_force:
                    results.append((item, analysis))
                    print(f"  [OK] [{analysis.direction}] {item.title[:30]}... "
                          f"(力度:{analysis.magnitude:.0f}, 类型:{analysis.force_type})")
        
        return results
    
    def _restore_analysis_from_record(self, record) -> ForceAnalysisResult:
        """
        从数据库记录恢复分析结果
        
        Args:
            record: NewsRecord对象
            
        Returns:
            ForceAnalysisResult对象
        """
        if record.analysis_result:
            try:
                data = json.loads(record.analysis_result)
                return ForceAnalysisResult(
                    is_force=data.get('is_force', True),
                    direction=data.get('direction', record.direction),
                    magnitude=data.get('magnitude', record.magnitude),
                    force_type=data.get('force_type', record.force_type),
                    confidence=data.get('confidence', record.confidence),
                    affected_symbols=data.get('affected_symbols', []),
                    affected_sectors=data.get('affected_sectors', []),
                    reason=data.get('reason', ''),
                    keywords=data.get('keywords', [])
                )
            except:
                pass
        
        return ForceAnalysisResult(
            is_force=True,
            direction=record.direction,
            magnitude=record.magnitude,
            force_type=record.force_type,
            confidence=record.confidence,
            affected_symbols=[],
            affected_sectors=[],
            reason='',
            keywords=[]
        )
    
    def _save_analysis_to_db(self, item: RSSItem, analysis: ForceAnalysisResult):
        """
        保存分析结果到数据库
        
        Args:
            item: RSSItem对象
            analysis: ForceAnalysisResult对象
        """
        # 先确保新闻存在于数据库
        # 使用稳定的guid（如果item.guid已经是稳定的就直接用，否则生成）
        stable_guid = item.guid if len(item.guid) == 32 else self._generate_stable_guid(item)
        news_data = {
            'guid': stable_guid,
            'title': item.title,
            'description': item.description,
            'link': item.link,
            'pub_date': item.pub_date.isoformat() if item.pub_date else '',
            'source_name': item.source or 'cls',
            'source_url': ''
        }
        self.db.add_news([news_data])
        
        # 获取新闻ID并更新分析结果
        record = self.db.get_news_by_guid(news_data['guid'])
        if record:
            self.db.update_analysis(record.id, analysis.to_dict())
    
    def create_forces(self, results: List[Tuple[RSSItem, ForceAnalysisResult]]) -> List[Dict]:
        """
        将分析结果转换为Force参数字典
        
        Args:
            results: (新闻, 分析结果) 列表
            
        Returns:
            Force参数字典列表
        """
        from stock_force_model import ForceDirection, ForceType
        
        forces = []
        
        # 衰减率映射
        decay_rates = {
            "long_term": 0.001,
            "mid_term": 0.01,
            "short_term": 0.1
        }
        
        # 方向映射
        direction_map = {
            "bullish": "BULLISH",
            "bearish": "BEARISH",
            "neutral": "NEUTRAL"
        }
        
        for news, analysis in results:
            force_dict = {
                "name": f"[{analysis.force_type}] {news.title[:40]}",
                "magnitude": analysis.magnitude,
                "direction": direction_map.get(analysis.direction, "NEUTRAL"),
                "force_type": analysis.force_type,
                "start_date": news.pub_date.isoformat(),
                "decay_rate": decay_rates.get(analysis.force_type, 0.1),
                "confidence": analysis.confidence,
                "source": f"rss:{news.source}",
                "affected_sectors": analysis.affected_sectors,
                "affected_symbols": analysis.affected_symbols,
                "reason": analysis.reason
            }
            forces.append(force_dict)
        
        return forces


def demo():
    """演示RSS获取和分析（含数据库功能）"""
    print("=" * 60)
    print("RSS新闻源分析演示（增强版）")
    print("=" * 60)
    
    # 创建整合器（使用本地规则分析器，不需要API Key）
    integrator = NewsForceIntegrator(use_llm=False)
    
    # 显示配置的RSS源
    print("\n【配置的RSS源】")
    for source in integrator.config.get_enabled_sources():
        print(f"  - {source['name']}: {source['url']}")
    
    # 运行增量分析
    print("\n【运行增量分析】")
    stats = integrator.run_incremental_analysis()
    
    # 获取最近的力量新闻
    print("\n【最近24小时的力量新闻】")
    recent_forces = integrator.get_recent_forces(hours=24, limit=10)
    
    if recent_forces:
        for news, analysis in recent_forces:
            direction_cn = {
                "bullish": "利多 ↑",
                "bearish": "利空 ↓",
                "neutral": "中性 →"
            }
            print(f"\n  [{direction_cn.get(analysis.direction, '未知')}] {news.title[:40]}")
            print(f"    力度: {analysis.magnitude:.0f}, 类型: {analysis.force_type}")
    else:
        print("  暂无力量新闻")
    
    # 显示数据库统计
    print("\n【数据库统计】")
    db_stats = integrator.get_statistics()
    print(f"  总新闻数: {db_stats['total_news']}")
    print(f"  已分析: {db_stats['analyzed_news']}")
    print(f"  可作为力: {db_stats['force_news']}")
    print(f"  今日获取: {db_stats['today_fetched']}")
    
    if db_stats.get('by_direction'):
        print("  按方向:")
        for d, cnt in db_stats['by_direction'].items():
            print(f"    {d}: {cnt}")


def demo_multi_source():
    """演示多RSS源功能"""
    print("=" * 60)
    print("多RSS源配置演示")
    print("=" * 60)
    
    from rss_database import ConfigManager
    
    config = ConfigManager()
    
    print("\n【当前配置的RSS源】")
    all_sources = config.config.get('rss_sources', [])
    for s in all_sources:
        status = "[ON]" if s.get('enabled', True) else "[OFF]"
        print(f"  {status} {s['name']} (优先级:{s.get('priority', 10)})")
        print(f"      {s['url']}")
    
    print("\n【启用/禁用示例】")
    print("  config.toggle_source('金十数据', True)   # 启用")
    print("  config.toggle_source('金十数据', False)  # 禁用")
    
    print("\n【添加新源示例】")
    print("  config.add_source('新浪财经', 'https://rsshub.app/sina/finance')")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--multi":
        demo_multi_source()
    else:
        demo()
