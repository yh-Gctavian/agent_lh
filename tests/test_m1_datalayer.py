# -*- coding: utf-8 -*-
"""M1数据层BUG检测脚本"""

import sys
sys.path.insert(0, 'wave_bottom_strategy')

print('=== M1数据层模块测试 ===')

# 测试1: DataLoader初始化
try:
    from data.loader import DataLoader
    loader = DataLoader()
    print('✓ [PASS] DataLoader初始化成功')
except Exception as e:
    print(f'✗ [FAIL] DataLoader初始化失败: {e}')

# 测试2: DataProcessor初始化
try:
    from data.processor import DataProcessor
    processor = DataProcessor()
    print('✓ [PASS] DataProcessor初始化成功')
except Exception as e:
    print(f'✗ [FAIL] DataProcessor初始化失败: {e}')

# 测试3: DataCache初始化
try:
    from data.cache import DataCache
    cache = DataCache()
    print('✓ [PASS] DataCache初始化成功')
except Exception as e:
    print(f'✗ [FAIL] DataCache初始化失败: {e}')

# 测试4: 数据加载功能
try:
    df = loader.load_daily_data('000001', '20200101', '20251231')
    if len(df) > 0:
        print(f'✓ [PASS] 数据加载成功: {len(df)}条')
    else:
        print('✗ [BUG-001] 数据加载返回空DataFrame')
except Exception as e:
    print(f'✗ [BUG-001] 数据加载异常: {e}')

# 测试5: 股票池加载
try:
    pool = loader.load_stock_pool('hs300')
    if len(pool) > 0:
        print(f'✓ [PASS] 股票池加载成功: {len(pool)}只')
    else:
        print('✗ [BUG-002] 股票池加载返回空列表')
except Exception as e:
    print(f'✗ [BUG-002] 股票池加载异常: {e}')

# 测试6: 数据预处理
try:
    test_data = df.copy()
    processed = processor.adjust_prices(test_data, 'qfq')
    print(f'✓ [PASS] 复权处理成功')
except Exception as e:
    print(f'✗ [FAIL] 复权处理失败: {e}')

# 测试7: 停牌标记
try:
    marked = processor.mark_suspended(test_data)
    print(f'✓ [PASS] 停牌标记成功')
except Exception as e:
    print(f'✗ [FAIL] 停牌标记失败: {e}')

# 测试8: 数据缓存
try:
    cache.save(df, 'test_cache')
    loaded = cache.load('test_cache')
    if len(loaded) > 0:
        print(f'✓ [PASS] 缓存读写成功')
    else:
        print('✗ [FAIL] 缓存读取返回空')
except Exception as e:
    print(f'✗ [FAIL] 缓存读写失败: {e}')

# 测试9: 数据验证
try:
    is_valid = loader.validate_data(df)
    if is_valid:
        print(f'✓ [PASS] 数据验证通过')
    else:
        print('✗ [FAIL] 数据验证失败')
except Exception as e:
    print(f'✗ [FAIL] 数据验证异常: {e}')

print('\n=== 测试完成 ===')