# -*- coding: utf-8 -*-
"""
测试数据准备脚本

从 AKShare 获取 A股 2020-2025 日K线数据
用于参数优化测试

创建日期：2026-04-04
编写人：量化测试经理 (mZ9QZZ)
"""

import akshare as ak
import pandas as pd
import os
from datetime import datetime
import time

# 数据存储路径
DATA_DIR = "data/daily"
CACHE_DIR = "data/cache"

# 数据时间范围
TRAIN_START = "2020-01-01"
TRAIN_END = "2023-12-31"
TEST_START = "2024-01-01"
TEST_END = "2025-12-31"

# 股票池：沪深300成分股
STOCK_POOL_FILE = "data/stock_pool.csv"


def ensure_dirs():
    """确保数据目录存在"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)
    print(f"✓ 数据目录已创建: {DATA_DIR}, {CACHE_DIR}")


def download_stock_list():
    """下载沪深300成分股列表"""
    try:
        # 获取沪深300成分股
        stock_list = ak.index_stock_cons_weight_csindex(symbol="000300")
        stock_list.to_csv(STOCK_POOL_FILE, index=False, encoding='utf-8')
        print(f"✓ 沪深300成分股列表已保存: {STOCK_POOL_FILE}")
        print(f"  共 {len(stock_list)} 只股票")
        return stock_list
    except Exception as e:
        print(f"⚠ 下载股票列表失败: {e}")
        return None


def download_daily_data(stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """下载单只股票日K线数据
    
    Args:
        stock_code: 股票代码（如 000001）
        start_date: 起始日期（如 20200101）
        end_date: 结束日期（如 20251231）
    
    Returns:
        日K线数据 DataFrame
    """
    try:
        # AKShare 日K线接口
        # 注意：股票代码格式需要调整（去掉交易所后缀）
        symbol = stock_code.split('.')[0] if '.' in stock_code else stock_code
        
        # 使用 stock_zh_a_hist 接口
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date.replace('-', ''),
            end_date=end_date.replace('-', ''),
            adjust="qfq"  # 前复权
        )
        
        # 标准化列名
        df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'turn', 'amplitude', 'change_pct', 'change_amount', 'turnover']
        
        # 重命名以符合项目规范
        df = df.rename(columns={
            'date': 'trade_date',
            'turn': 'turnover_rate',
            'change_pct': 'pct_change'
        })
        
        return df
    except Exception as e:
        print(f"⚠ 下载 {stock_code} 数据失败: {e}")
        return None


def download_all_stocks(stock_list: pd.DataFrame, start_date: str, end_date: str, max_stocks: int = 50):
    """批量下载股票数据
    
    Args:
        stock_list: 股票列表 DataFrame
        start_date: 起始日期
        end_date: 结束日期
        max_stocks: 最大下载股票数（测试阶段限制数量）
    """
    codes = stock_list['成分券代码'].tolist()[:max_stocks]
    
    success_count = 0
    fail_count = 0
    
    for i, code in enumerate(codes):
        print(f"[{i+1}/{len(codes)}] 正在下载 {code}...")
        
        df = download_daily_data(code, start_date, end_date)
        
        if df is not None and len(df) > 0:
            # 保存到 Parquet
            file_path = os.path.join(DATA_DIR, f"stock_{code}.parquet")
            df.to_parquet(file_path, index=False)
            print(f"  ✓ 已保存: {file_path} ({len(df)} 条记录)")
            success_count += 1
        else:
            fail_count += 1
        
        # 避免请求过快
        time.sleep(0.5)
    
    print(f"\n✓ 批量下载完成: 成功 {success_count}, 失败 {fail_count}")
    
    # 记录下载摘要
    summary = {
        "total_stocks": len(codes),
        "success_count": success_count,
        "fail_count": fail_count,
        "start_date": start_date,
        "end_date": end_date,
        "download_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    summary_df = pd.DataFrame([summary])
    summary_df.to_csv(os.path.join(CACHE_DIR, "download_summary.csv"), index=False)
    
    return success_count, fail_count


def verify_data_integrity():
    """验证数据完整性
    
    检查下载的数据文件是否符合测试要求
    """
    files = os.listdir(DATA_DIR)
    parquet_files = [f for f in files if f.endswith('.parquet')]
    
    print(f"\n数据验证:")
    print(f"  数据文件数: {len(parquet_files)}")
    
    # 检查时间范围
    for f in parquet_files[:3]:  # 只检查前3个作为示例
        df = pd.read_parquet(os.path.join(DATA_DIR, f))
        print(f"  {f}: {df['trade_date'].min()} ~ {df['trade_date'].max()}, {len(df)} 条")
    
    return len(parquet_files)


def prepare_test_data(sample_size: int = 30):
    """准备测试数据
    
    Args:
        sample_size: 测试样本股票数量（默认30只，足够参数优化测试）
    """
    print("=" * 50)
    print("测试数据准备 - AKShare 数据源")
    print("=" * 50)
    
    # 1. 创建目录
    ensure_dirs()
    
    # 2. 下载股票列表
    stock_list = download_stock_list()
    
    if stock_list is None:
        print("⚠ 无法获取股票列表，使用备用方案")
        # 备用：使用部分已知股票代码
        backup_codes = ['000001', '000002', '000004', '000006', '000007',
                        '000008', '000009', '000010', '000011', '000012']
        stock_list = pd.DataFrame({'成分券代码': backup_codes})
    
    # 3. 批量下载日K线数据（限制数量以加快测试）
    print(f"\n开始下载 {sample_size} 只股票的日K线数据...")
    print(f"时间范围: {TRAIN_START} ~ {TEST_END}")
    
    download_all_stocks(
        stock_list,
        start_date=TRAIN_START,
        end_date=TEST_END,
        max_stocks=sample_size
    )
    
    # 4. 验证数据完整性
    file_count = verify_data_integrity()
    
    print(f"\n" + "=" * 50)
    print(f"✓ 测试数据准备完成！")
    print(f"  数据文件: {file_count} 个")
    print(f"  时间范围: {TRAIN_START} ~ {TEST_END}")
    print(f"  存储路径: {DATA_DIR}")
    print("=" * 50)


if __name__ == "__main__":
    # 执行数据准备（测试阶段使用30只股票）
    prepare_test_data(sample_size=30)