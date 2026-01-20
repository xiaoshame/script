#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置验证工具

验证config.json配置是否正确，检查所有必要的参数
"""

import json
from pathlib import Path
import os


def validate_config(config_path: str = "config.json") -> bool:
    """
    验证配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        是否有效
    """
    print(f"验证配置文件: {config_path}")
    print("=" * 60)
    
    # 检查文件是否存在
    if not Path(config_path).exists():
        print(f"❌ 错误: 配置文件不存在 ({config_path})")
        return False
    
    # 加载JSON
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("✓ JSON格式有效")
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return False
    
    # 验证股票配置
    print("\n【股票配置】")
    stocks = config.get('stocks', [])
    if not stocks:
        print("⚠ 警告: 没有配置股票")
    else:
        print(f"✓ 共 {len(stocks)} 只股票配置:")
        enabled_count = 0
        for s in stocks:
            symbol = s.get('symbol', '未知')
            name = s.get('name', symbol)
            enabled = s.get('enabled', True)
            entity_type = s.get('entity_type', 'stock')
            status = "启用" if enabled else "禁用"
            print(f"  • {symbol} {name} [{entity_type}] ({status})")
            if enabled:
                enabled_count += 1
        print(f"  → 启用的股票: {enabled_count} 只")
    
    # 验证RSS源配置
    print("\n【RSS源配置】")
    sources = config.get('rss_sources', [])
    if not sources:
        print("⚠ 警告: 没有配置RSS源")
    else:
        print(f"✓ 共 {len(sources)} 个RSS源配置:")
        enabled_count = 0
        for s in sources:
            name = s.get('name', '未知')
            url = s.get('url', '')
            enabled = s.get('enabled', True)
            priority = s.get('priority', 10)
            status = "启用" if enabled else "禁用"
            print(f"  • {name} (优先级{priority}) [{status}]")
            print(f"    URL: {url[:50]}...")
            if enabled:
                enabled_count += 1
        print(f"  → 启用的源: {enabled_count} 个")
    
    # 验证数据库配置
    print("\n【数据库配置】")
    db_config = config.get('database', {})
    db_path = db_config.get('path', 'rss_news.db')
    max_age = db_config.get('max_age_days', 30)
    print(f"✓ 数据库路径: {db_path}")
    print(f"✓ 最大保存天数: {max_age}")
    if Path(db_path).exists():
        size_mb = Path(db_path).stat().st_size / (1024*1024)
        print(f"  → 当前数据库大小: {size_mb:.2f} MB")
    
    # 验证分析配置
    print("\n【分析配置】")
    analysis_cfg = config.get('analysis', {})
    print(f"✓ 每源最大获取条数: {analysis_cfg.get('max_items_per_source', 100)}")
    print(f"✓ 批处理大小: {analysis_cfg.get('batch_size', 999)}")
    print(f"✓ 请求延迟: {analysis_cfg.get('request_delay', 0.5)}秒")
    print(f"✓ 最大并发数: {analysis_cfg.get('max_concurrent_requests', 2)}")
    
    # 验证LLM配置
    print("\n【大模型配置】")
    llm_cfg = config.get('llm', {})
    if not llm_cfg:
        print("⚠ 警告: 没有大模型配置")
    else:
        enabled = llm_cfg.get('enabled', False)
        status = "启用" if enabled else "禁用"
        print(f"✓ 状态: {status}")
        print(f"✓ 提供商: {llm_cfg.get('provider', '未知')}")
        print(f"✓ 模型: {llm_cfg.get('model', '未知')}")
        print(f"✓ API Base URL: {llm_cfg.get('base_url', '默认')}")
        print(f"✓ 超时时间: {llm_cfg.get('timeout', 30)}秒")
        
        # 检查API Key
        api_key = llm_cfg.get('api_key', '')
        if api_key.startswith('${') and api_key.endswith('}'):
            env_var = api_key[2:-1]
            print(f"  环境变量引用: {env_var}")
            value = os.environ.get(env_var, '')
            if value:
                print(f"  ✓ 环境变量已设置 (值: {value[:20]}...)")
            else:
                print(f"  ❌ 环境变量未设置: {env_var}")
        elif api_key:
            print(f"  ✓ 直接配置API Key (值: {api_key[:20]}...)")
        else:
            print(f"  ❌ API Key未配置")
    
    # 最终结论
    print("\n" + "=" * 60)
    print("✅ 配置验证完成!")
    
    # 给出建议
    if not stocks or len([s for s in stocks if s.get('enabled', True)]) == 0:
        print("⚠ 建议: 至少启用一只股票进行分析")
    
    if not sources or len([s for s in sources if s.get('enabled', True)]) == 0:
        print("⚠ 建议: 至少启用一个RSS源获取新闻")
    
    if llm_cfg.get('enabled') and not os.environ.get(
        llm_cfg.get('api_key', '')[2:-1] 
        if llm_cfg.get('api_key', '').startswith('${') else 'DUMMY'
    ):
        print("⚠ 建议: 设置GEMINI_API_KEY环境变量以使用大模型")
    
    return True


def show_sample_config():
    """显示示例配置"""
    print("""
【config.json 示例结构】

{
    "stocks": [
        {
            "symbol": "600519",
            "name": "贵州茅台",
            "entity_type": "stock",
            "enabled": true
        }
    ],
    "rss_sources": [
        {
            "name": "财联社热点",
            "url": "https://rsshub.rss.zgdnz.cc/cls/hot",
            "enabled": true,
            "category": "财经",
            "priority": 1
        }
    ],
    "database": {
        "path": "rss_news.db",
        "max_age_days": 30
    },
    "analysis": {
        "max_items_per_source": 100,
        "batch_size": 999,
        "request_delay": 0.5
    },
    "llm": {
        "enabled": true,
        "api_key": "${GEMINI_API_KEY}",
        "model": "gemini-3-flash-preview"
    }
}
    """)


if __name__ == "__main__":
    import sys
    
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    
    print("""
╔══════════════════════════════════════════════════════════╗
║           配置文件验证工具 (Config Validator)             ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    validate_config(config_path)
    
    if len(sys.argv) > 2 and sys.argv[2] == "--sample":
        show_sample_config()
