# -*- coding: utf-8 -*-
"""
RSS新闻数据库模块

使用SQLite存储RSS新闻和分析结果，支持：
- 新闻去重
- 增量处理
- 历史查询
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import threading


@dataclass
class NewsRecord:
    """新闻记录"""
    id: int = 0
    guid: str = ""
    title: str = ""
    description: str = ""
    link: str = ""
    pub_date: str = ""
    source_name: str = ""
    source_url: str = ""
    fetched_at: str = ""
    analyzed: bool = False
    analysis_result: str = ""  # JSON格式的分析结果
    is_force: bool = False
    direction: str = ""
    magnitude: float = 0.0
    force_type: str = ""
    confidence: float = 0.0


class RSSDatabase:
    """
    RSS新闻数据库
    
    使用SQLite存储新闻和分析结果
    """
    
    _local = threading.local()
    
    def __init__(self, db_path: str = "rss_news.db"):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取当前线程的数据库连接"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(str(self.db_path))
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection
    
    def _init_db(self):
        """初始化数据库表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 新闻表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guid TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                link TEXT,
                pub_date TEXT,
                source_name TEXT,
                source_url TEXT,
                fetched_at TEXT NOT NULL,
                analyzed INTEGER DEFAULT 0,
                analysis_result TEXT,
                is_force INTEGER DEFAULT 0,
                direction TEXT,
                magnitude REAL DEFAULT 0,
                force_type TEXT,
                confidence REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_guid ON news(guid)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_analyzed ON news(analyzed)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_pub_date ON news(pub_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_source ON news(source_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_is_force ON news(is_force)')
        
        # RSS源配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rss_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                url TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                category TEXT,
                priority INTEGER DEFAULT 10,
                description TEXT,
                last_fetch TEXT,
                fetch_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 运行日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS run_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_time TEXT NOT NULL,
                sources_count INTEGER DEFAULT 0,
                news_fetched INTEGER DEFAULT 0,
                news_new INTEGER DEFAULT 0,
                news_analyzed INTEGER DEFAULT 0,
                forces_generated INTEGER DEFAULT 0,
                duration_seconds REAL DEFAULT 0,
                status TEXT,
                error_message TEXT
            )
        ''')
        
        conn.commit()
    
    def add_news(self, news_list: List[Dict]) -> Tuple[int, int, List[Dict]]:
        """
        批量添加新闻
        
        Args:
            news_list: 新闻字典列表，每个包含:
                - guid: 唯一标识
                - title: 标题
                - description: 描述
                - link: 链接
                - pub_date: 发布日期
                - source_name: 来源名称
                - source_url: 来源URL
                
        Returns:
            (添加数量, 跳过数量, 跳过的新闻列表)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        added = 0
        skipped = 0
        skipped_news = []
        now = datetime.now().isoformat()
        
        for news in news_list:
            try:
                cursor.execute('''
                    INSERT INTO news (guid, title, description, link, pub_date, 
                                     source_name, source_url, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    news.get('guid', ''),
                    news.get('title', ''),
                    news.get('description', ''),
                    news.get('link', ''),
                    news.get('pub_date', ''),
                    news.get('source_name', ''),
                    news.get('source_url', ''),
                    now
                ))
                added += 1
            except sqlite3.IntegrityError:
                # guid重复，跳过
                skipped += 1
                skipped_news.append(news)
        
        conn.commit()
        return added, skipped, skipped_news
    
    def get_news_by_guid(self, guid: str) -> Optional[NewsRecord]:
        """
        根据guid获取新闻记录
        
        Args:
            guid: 新闻唯一标识
            
        Returns:
            NewsRecord或None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM news WHERE guid = ?', (guid,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_record(row)
        return None
    
    def get_unanalyzed_news(self, limit: int = 50) -> List[NewsRecord]:
        """
        获取未分析的新闻
        
        Args:
            limit: 最大返回数量
            
        Returns:
            NewsRecord列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM news 
            WHERE analyzed = 0 
            ORDER BY pub_date DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        return [self._row_to_record(row) for row in rows]
    
    def get_analyzed_guids(self) -> List[str]:
        """
        获取所有已分析新闻的guid列表
        
        用于初始化内存缓存，避免重复分析
        
        Returns:
            guid字符串列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT guid FROM news WHERE analyzed = 1')
        rows = cursor.fetchall()
        
        return [row['guid'] for row in rows]
    
    def update_analysis(self, news_id: int, analysis: Dict):
        """
        更新新闻分析结果
        
        Args:
            news_id: 新闻ID
            analysis: 分析结果字典
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE news SET
                analyzed = 1,
                analysis_result = ?,
                is_force = ?,
                direction = ?,
                magnitude = ?,
                force_type = ?,
                confidence = ?
            WHERE id = ?
        ''', (
            json.dumps(analysis, ensure_ascii=False),
            1 if analysis.get('is_force', False) else 0,
            analysis.get('direction', ''),
            analysis.get('magnitude', 0),
            analysis.get('force_type', ''),
            analysis.get('confidence', 0),
            news_id
        ))
        
        conn.commit()
    
    def batch_update_analysis(self, updates: List[Tuple[int, Dict]]):
        """
        批量更新分析结果
        
        Args:
            updates: [(news_id, analysis_dict), ...] 列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        for news_id, analysis in updates:
            cursor.execute('''
                UPDATE news SET
                    analyzed = 1,
                    analysis_result = ?,
                    is_force = ?,
                    direction = ?,
                    magnitude = ?,
                    force_type = ?,
                    confidence = ?
                WHERE id = ?
            ''', (
                json.dumps(analysis, ensure_ascii=False),
                1 if analysis.get('is_force', False) else 0,
                analysis.get('direction', ''),
                analysis.get('magnitude', 0),
                analysis.get('force_type', ''),
                analysis.get('confidence', 0),
                news_id
            ))
        
        conn.commit()
    
    def get_force_news(self, 
                       since: datetime = None, 
                       direction: str = None,
                       force_type: str = None,
                       limit: int = 100) -> List[NewsRecord]:
        """
        获取可作为力的新闻
        
        Args:
            since: 起始时间
            direction: 方向筛选 (bullish/bearish/neutral)
            force_type: 类型筛选 (long_term/mid_term/short_term)
            limit: 最大返回数量
            
        Returns:
            NewsRecord列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM news WHERE is_force = 1'
        params = []
        
        if since:
            query += ' AND pub_date >= ?'
            params.append(since.isoformat())
        
        if direction:
            query += ' AND direction = ?'
            params.append(direction)
        
        if force_type:
            query += ' AND force_type = ?'
            params.append(force_type)
        
        query += ' ORDER BY pub_date DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [self._row_to_record(row) for row in rows]
    
    def get_news_by_source(self, source_name: str, limit: int = 50) -> List[NewsRecord]:
        """
        按来源获取新闻
        
        Args:
            source_name: 来源名称
            limit: 最大返回数量
            
        Returns:
            NewsRecord列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM news 
            WHERE source_name = ? 
            ORDER BY pub_date DESC 
            LIMIT ?
        ''', (source_name, limit))
        
        rows = cursor.fetchall()
        return [self._row_to_record(row) for row in rows]
    
    def get_statistics(self) -> Dict:
        """
        获取数据库统计信息
        
        Returns:
            统计信息字典
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # 总新闻数
        cursor.execute('SELECT COUNT(*) FROM news')
        stats['total_news'] = cursor.fetchone()[0]
        
        # 已分析数
        cursor.execute('SELECT COUNT(*) FROM news WHERE analyzed = 1')
        stats['analyzed_news'] = cursor.fetchone()[0]
        
        # 未分析数
        stats['unanalyzed_news'] = stats['total_news'] - stats['analyzed_news']
        
        # 可作为力的新闻数
        cursor.execute('SELECT COUNT(*) FROM news WHERE is_force = 1')
        stats['force_news'] = cursor.fetchone()[0]
        
        # 按方向统计
        cursor.execute('''
            SELECT direction, COUNT(*) as cnt 
            FROM news WHERE is_force = 1 
            GROUP BY direction
        ''')
        stats['by_direction'] = {row['direction']: row['cnt'] for row in cursor.fetchall()}
        
        # 按类型统计
        cursor.execute('''
            SELECT force_type, COUNT(*) as cnt 
            FROM news WHERE is_force = 1 
            GROUP BY force_type
        ''')
        stats['by_force_type'] = {row['force_type']: row['cnt'] for row in cursor.fetchall()}
        
        # 按来源统计
        cursor.execute('''
            SELECT source_name, COUNT(*) as cnt 
            FROM news 
            GROUP BY source_name
        ''')
        stats['by_source'] = {row['source_name']: row['cnt'] for row in cursor.fetchall()}
        
        # 今日新增
        today = datetime.now().date().isoformat()
        cursor.execute('''
            SELECT COUNT(*) FROM news 
            WHERE DATE(fetched_at) = ?
        ''', (today,))
        stats['today_fetched'] = cursor.fetchone()[0]
        
        return stats
    
    def cleanup_old_news(self, days: int = 30):
        """
        清理旧新闻
        
        Args:
            days: 保留天数
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('''
            DELETE FROM news WHERE pub_date < ?
        ''', (cutoff,))
        
        deleted = cursor.rowcount
        conn.commit()
        
        print(f"[Database] 清理了 {deleted} 条旧新闻（{days}天前）")
        return deleted
    
    def log_run(self, 
                sources_count: int = 0,
                news_fetched: int = 0,
                news_new: int = 0,
                news_analyzed: int = 0,
                forces_generated: int = 0,
                duration: float = 0,
                status: str = "success",
                error: str = None):
        """
        记录运行日志
        
        Args:
            sources_count: 处理的源数量
            news_fetched: 获取的新闻数
            news_new: 新增的新闻数
            news_analyzed: 分析的新闻数
            forces_generated: 生成的力数量
            duration: 运行时长(秒)
            status: 状态
            error: 错误信息
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO run_logs 
            (run_time, sources_count, news_fetched, news_new, 
             news_analyzed, forces_generated, duration_seconds, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            sources_count,
            news_fetched,
            news_new,
            news_analyzed,
            forces_generated,
            duration,
            status,
            error
        ))
        
        conn.commit()
    
    def get_recent_runs(self, limit: int = 10) -> List[Dict]:
        """
        获取最近的运行记录
        
        Args:
            limit: 返回数量
            
        Returns:
            运行记录列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM run_logs 
            ORDER BY run_time DESC 
            LIMIT ?
        ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def _row_to_record(self, row: sqlite3.Row) -> NewsRecord:
        """将数据库行转换为NewsRecord"""
        return NewsRecord(
            id=row['id'],
            guid=row['guid'],
            title=row['title'],
            description=row['description'] or '',
            link=row['link'] or '',
            pub_date=row['pub_date'] or '',
            source_name=row['source_name'] or '',
            source_url=row['source_url'] or '',
            fetched_at=row['fetched_at'] or '',
            analyzed=bool(row['analyzed']),
            analysis_result=row['analysis_result'] or '',
            is_force=bool(row['is_force']),
            direction=row['direction'] or '',
            magnitude=row['magnitude'] or 0.0,
            force_type=row['force_type'] or '',
            confidence=row['confidence'] or 0.0
        )
    
    def close(self):
        """关闭数据库连接"""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None


class ConfigManager:
    """
    配置管理器
    
    读取和管理 config.json 配置文件
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        if not self.config_path.exists():
            print(f"[Config] 配置文件不存在: {self.config_path}")
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"[Config] 加载配置文件: {self.config_path}")
                return config
        except Exception as e:
            print(f"[Config] 加载配置失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "stocks": [
                {
                    "symbol": "600519",
                    "name": "贵州茅台",
                    "entity_type": "stock",
                    "enabled": True
                }
            ],
            "rss_sources": [
                {
                    "name": "财联社热点",
                    "url": "https://rsshub.rss.zgdnz.cc/cls/hot",
                    "enabled": True,
                    "category": "财经",
                    "priority": 1
                }
            ],
            "database": {
                "path": "rss_news.db",
                "max_age_days": 30
            },
            "analysis": {
                "max_items_per_source": 20,
                "batch_size": 10,
                "request_delay": 0.5
            }
        }
    
    def get_enabled_stocks(self) -> List[Dict]:
        """获取启用的股票列表"""
        stocks = self.config.get('stocks', [])
        enabled = [s for s in stocks if s.get('enabled', True)]
        return enabled
    
    def get_all_stocks(self) -> List[Dict]:
        """获取所有股票列表"""
        return self.config.get('stocks', [])
    
    def get_enabled_sources(self) -> List[Dict]:
        """获取启用的RSS源列表"""
        sources = self.config.get('rss_sources', [])
        enabled = [s for s in sources if s.get('enabled', True)]
        # 按优先级排序
        enabled.sort(key=lambda x: x.get('priority', 10))
        return enabled
    
    def get_llm_config(self) -> Dict:
        """获取大模型配置"""
        return self.config.get('llm', {})
    
    def get_database_config(self) -> Dict:
        """获取数据库配置"""
        return self.config.get('database', {})
    
    def get_analysis_config(self) -> Dict:
        """获取分析配置"""
        return self.config.get('analysis', {})
    
    def add_source(self, name: str, url: str, **kwargs):
        """添加新的RSS源"""
        sources = self.config.get('rss_sources', [])
        
        # 检查是否已存在
        for s in sources:
            if s['name'] == name:
                print(f"[Config] RSS源已存在: {name}")
                return False
        
        new_source = {
            "name": name,
            "url": url,
            "enabled": kwargs.get('enabled', True),
            "category": kwargs.get('category', '财经'),
            "priority": kwargs.get('priority', 10),
            "description": kwargs.get('description', '')
        }
        
        sources.append(new_source)
        self.config['rss_sources'] = sources
        self._save_config()
        
        print(f"[Config] 添加RSS源: {name}")
        return True
    
    def remove_source(self, name: str) -> bool:
        """移除RSS源"""
        sources = self.config.get('rss_sources', [])
        new_sources = [s for s in sources if s['name'] != name]
        
        if len(new_sources) == len(sources):
            print(f"[Config] RSS源不存在: {name}")
            return False
        
        self.config['rss_sources'] = new_sources
        self._save_config()
        
        print(f"[Config] 移除RSS源: {name}")
        return True
    
    def toggle_source(self, name: str, enabled: bool = None) -> bool:
        """启用/禁用RSS源"""
        sources = self.config.get('rss_sources', [])
        
        for s in sources:
            if s['name'] == name:
                if enabled is None:
                    s['enabled'] = not s.get('enabled', True)
                else:
                    s['enabled'] = enabled
                self._save_config()
                status = "启用" if s['enabled'] else "禁用"
                print(f"[Config] {status}RSS源: {name}")
                return True
        
        print(f"[Config] RSS源不存在: {name}")
        return False
    
    def _save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[Config] 保存配置失败: {e}")
    
    def reload(self):
        """重新加载配置"""
        self.config = self._load_config()


def demo():
    """演示数据库功能"""
    print("=" * 60)
    print("RSS数据库功能演示")
    print("=" * 60)
    
    # 初始化
    db = RSSDatabase("test_rss.db")
    config = ConfigManager()
    
    # 显示配置的RSS源
    print("\n【配置的RSS源】")
    for source in config.get_enabled_sources():
        print(f"  • {source['name']}: {source['url']}")
    
    # 添加测试新闻
    print("\n【添加测试新闻】")
    test_news = [
        {
            "guid": "test-001",
            "title": "央行宣布降息25个基点",
            "description": "中国人民银行今日宣布下调贷款市场报价利率25个基点",
            "link": "https://example.com/1",
            "pub_date": datetime.now().isoformat(),
            "source_name": "财联社热点",
            "source_url": "https://rsshub.rss.zgdnz.cc/cls/hot"
        },
        {
            "guid": "test-002",
            "title": "某公司业绩暴雷",
            "description": "某上市公司发布业绩预告，净利润同比下降80%",
            "link": "https://example.com/2",
            "pub_date": datetime.now().isoformat(),
            "source_name": "财联社热点",
            "source_url": "https://rsshub.rss.zgdnz.cc/cls/hot"
        }
    ]
    
    added, skipped, _ = db.add_news(test_news)
    print(f"  添加: {added}, 跳过: {skipped}")
    
    # 获取未分析的新闻
    print("\n【未分析的新闻】")
    unanalyzed = db.get_unanalyzed_news(limit=5)
    for news in unanalyzed:
        print(f"  [{news.id}] {news.title}")
    
    # 模拟分析并更新
    if unanalyzed:
        print("\n【更新分析结果】")
        analysis = {
            "is_force": True,
            "direction": "bullish",
            "magnitude": 75,
            "force_type": "long_term",
            "confidence": 0.85,
            "reason": "央行降息利好股市"
        }
        db.update_analysis(unanalyzed[0].id, analysis)
        print(f"  更新了新闻 [{unanalyzed[0].id}] 的分析结果")
    
    # 统计信息
    print("\n【数据库统计】")
    stats = db.get_statistics()
    print(f"  总新闻数: {stats['total_news']}")
    print(f"  已分析: {stats['analyzed_news']}")
    print(f"  未分析: {stats['unanalyzed_news']}")
    print(f"  可作为力: {stats['force_news']}")
    
    # 记录运行日志
    db.log_run(
        sources_count=1,
        news_fetched=2,
        news_new=2,
        news_analyzed=1,
        forces_generated=1,
        duration=1.5,
        status="success"
    )
    
    # 显示运行记录
    print("\n【最近运行记录】")
    runs = db.get_recent_runs(5)
    for run in runs:
        print(f"  {run['run_time']}: 获取{run['news_fetched']}条, "
              f"新增{run['news_new']}条, 分析{run['news_analyzed']}条")
    
    db.close()
    print("\n演示完成")


if __name__ == "__main__":
    demo()
