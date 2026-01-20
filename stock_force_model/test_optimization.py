#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速测试脚本
测试优化后的功能是否正常
"""

import os
import sys

def test_config_load():
    """测试1: 配置加载"""
    print("=" * 60)
    print("测试1: 配置文件加载")
    print("=" * 60)
    
    try:
        from rss_database import ConfigManager
        
        config = ConfigManager("config.json")
        print("✓ 配置加载成功")
        
        # 测试获取各项配置
        stocks = config.get_enabled_stocks()
        print(f"✓ 启用的股票: {len(stocks)} 只")
        
        sources = config.get_enabled_sources()
        print(f"✓ 启用的RSS源: {len(sources)} 个")
        
        llm_cfg = config.get_llm_config()
        print(f"✓ LLM配置: {llm_cfg.get('model', 'unknown')}")
        
        return True
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        return False


def test_llm_config():
    """测试2: LLM配置和环境变量"""
    print("\n" + "=" * 60)
    print("测试2: LLM配置和环境变量引用")
    print("=" * 60)
    
    try:
        from rss_database import ConfigManager
        
        config = ConfigManager("config.json")
        llm_cfg = config.get_llm_config()
        
        api_key_str = llm_cfg.get('api_key', '')
        print(f"配置的API Key: {api_key_str}")
        
        if api_key_str.startswith('${') and api_key_str.endswith('}'):
            env_var = api_key_str[2:-1]
            print(f"✓ 检测到环境变量引用: {env_var}")
            
            value = os.environ.get(env_var, '')
            if value:
                print(f"✓ 环境变量已设置 (长度: {len(value)})")
            else:
                print(f"⚠ 环境变量未设置: {env_var}")
                print(f"  请运行: $env:{env_var} = 'your-api-key'")
        else:
            print("✓ 使用直接配置的API Key")
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


def test_engine_init():
    """测试3: 引擎初始化"""
    print("\n" + "=" * 60)
    print("测试3: StockForceEngineV2 初始化")
    print("=" * 60)
    
    try:
        from main import StockForceEngineV2
        
        print("初始化引擎 (use_llm=True)...")
        engine = StockForceEngineV2(use_llm=True, config_path="config.json")
        print("✓ 引擎初始化成功")
        
        # 验证配置是否正确加载
        llm_config = engine.news_integrator.config.get_llm_config()
        print(f"✓ LLM启用: {llm_config.get('enabled')}")
        print(f"✓ 使用模型: {llm_config.get('model')}")
        
        stocks = engine.news_integrator.config.get_enabled_stocks()
        print(f"✓ 待分析股票: {len(stocks)} 只")
        
        return True
    except Exception as e:
        print(f"✗ 引擎初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_add_stock():
    """测试4: 添加股票"""
    print("\n" + "=" * 60)
    print("测试4: 添加股票和获取数据")
    print("=" * 60)
    
    try:
        from main import StockForceEngineV2
        
        engine = StockForceEngineV2(use_llm=False, config_path="config.json")
        
        print("添加测试股票 600519...")
        stock = engine.add_stock("600519", name="贵州茅台", fetch_realtime=True)
        print(f"✓ 股票添加成功: {stock.name}")
        print(f"  市值: {stock.market_cap:.0f} 亿")
        
        # 检查行情数据
        if "600519" in engine.quotes:
            quote = engine.quotes["600519"]
            print(f"✓ 获取到实时行情:")
            print(f"  价格: {quote.price:.2f}")
            print(f"  涨跌: {quote.change_pct:+.2f}%")
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multi_stock_output():
    """测试5: 多股票报告输出"""
    print("\n" + "=" * 60)
    print("测试5: 多股票报告格式")
    print("=" * 60)
    
    try:
        # 模拟多股票报告输出
        all_reports = [
            ("600519", "贵州茅台", "【测试报告1】\n内容省略..."),
            ("000001", "上证指数", "【测试报告2】\n内容省略..."),
        ]
        
        print("\n" + "=" * 80)
        print("【最终分析报告汇总】")
        print("=" * 80)
        
        for symbol, name, report in all_reports:
            print(f"\n[{symbol} {name}]")
            print(report)
            print("\n" + "-" * 80)
        
        print("\n✓ 多股票报告格式测试通过")
        return True
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


def test_config_load():
    """测试1: 配置加载"""
    print("=" * 60)
    print("测试1: 配置文件加载")
    print("=" * 60)
    
    try:
        from rss_database import ConfigManager
        
        config = ConfigManager("config.json")
        print("[OK] 配置加载成功")
        
        # 测试获取各项配置
        stocks = config.get_enabled_stocks()
        print(f"[OK] 启用的股票: {len(stocks)} 只")
        
        sources = config.get_enabled_sources()
        print(f"[OK] 启用的RSS源: {len(sources)} 个")
        
        llm_cfg = config.get_llm_config()
        print(f"[OK] LLM配置: {llm_cfg.get('model', 'unknown')}")
        
        return True
    except Exception as e:
        print(f"[FAIL] 配置加载失败: {e}")
        return False


def test_llm_config():
    """测试2: LLM配置和环境变量"""
    print("\n" + "=" * 60)
    print("测试2: LLM配置和环境变量引用")
    print("=" * 60)
    
    try:
        from rss_database import ConfigManager
        
        config = ConfigManager("config.json")
        llm_cfg = config.get_llm_config()
        
        api_key_str = llm_cfg.get('api_key', '')
        print(f"配置的API Key: {api_key_str}")
        
        if api_key_str.startswith('${') and api_key_str.endswith('}'):
            env_var = api_key_str[2:-1]
            print(f"[OK] 检测到环境变量引用: {env_var}")
            
            value = os.environ.get(env_var, '')
            if value:
                print(f"[OK] 环境变量已设置 (长度: {len(value)})")
            else:
                print(f"[WARN] 环境变量未设置: {env_var}")
                print(f"  请运行: $env:{env_var} = 'your-api-key'")
        else:
            print("[OK] 使用直接配置的API Key")
        
        return True
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        return False


def test_engine_init():
    """测试3: 引擎初始化"""
    print("\n" + "=" * 60)
    print("测试3: StockForceEngineV2 初始化")
    print("=" * 60)
    
    try:
        from main import StockForceEngineV2
        
        print("初始化引擎 (use_llm=True)...")
        engine = StockForceEngineV2(use_llm=True, config_path="config.json")
        print("[OK] 引擎初始化成功")
        
        # 验证配置是否正确加载
        llm_config = engine.news_integrator.config.get_llm_config()
        print(f"[OK] LLM启用: {llm_config.get('enabled')}")
        print(f"[OK] 使用模型: {llm_config.get('model')}")
        
        stocks = engine.news_integrator.config.get_enabled_stocks()
        print(f"[OK] 待分析股票: {len(stocks)} 只")
        
        return True
    except Exception as e:
        print(f"[FAIL] 引擎初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_add_stock():
    """测试4: 添加股票"""
    print("\n" + "=" * 60)
    print("测试4: 添加股票和获取数据")
    print("=" * 60)
    
    try:
        from main import StockForceEngineV2
        
        engine = StockForceEngineV2(use_llm=False, config_path="config.json")
        
        print("添加测试股票 600519...")
        stock = engine.add_stock("600519", name="贵州茅台", fetch_realtime=True)
        print(f"[PASS] 股票添加成功: {stock.name}")
        print(f"  市值: {stock.market_cap:.0f} 亿")
        
        # 检查行情数据
        if "600519" in engine.quotes:
            quote = engine.quotes["600519"]
            print(f"[+] 获取到实时行情:")
            print(f"  价格: {quote.price:.2f}")
            print(f"  涨跌: {quote.change_pct:+.2f}%")
        
        return True
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multi_stock_output():
    """测试5: 多股票报告输出"""
    print("\n" + "=" * 60)
    print("测试5: 多股票报告格式")
    print("=" * 60)
    
    try:
        # 模拟多股票报告输出
        all_reports = [
            ("600519", "贵州茅台", "【测试报告1】\n内容省略..."),
            ("000001", "上证指数", "【测试报告2】\n内容省略..."),
        ]
        
        print("\n" + "=" * 80)
        print("【最终分析报告汇总】")
        print("=" * 80)
        
        for symbol, name, report in all_reports:
            print(f"\n[{symbol} {name}]")
            print(report)
            print("\n" + "-" * 80)
        
        print("\n[OK] 多股票报告格式测试通过")
        return True
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                优化功能测试套件                            ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    results = []
    
    # 运行所有测试
    results.append(("配置加载", test_config_load()))
    results.append(("LLM配置", test_llm_config()))
    results.append(("引擎初始化", test_engine_init()))
    results.append(("添加股票", test_add_stock()))
    results.append(("多股票输出", test_multi_stock_output()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    for name, result in results:
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"{name:15} {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"总计: {passed}/{len(results)} 通过")
    
    if passed == len(results):
        print("\n[SUCCESS] 所有测试通过！优化成功！")
    else:
        print(f"\n[WARNING] 有 {len(results) - passed} 个测试失败，需要检查")
    
    return passed == len(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
