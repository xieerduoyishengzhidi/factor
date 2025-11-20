# preprocess/align_data.py
import os
import sys
import pandas as pd

# 兼容直接运行和作为模块导入
try:
    from preprocess.load_data import load_data
except ImportError:
    # 如果作为脚本直接运行，使用相对导入
    sys.path.insert(0, os.path.dirname(__file__))
    from load_data import load_data


# 路径设置
ROOT = os.path.dirname(os.path.dirname(__file__))          # factor/
RAW_PATH = os.path.join(ROOT, 'data', 'raw')
INTERIM_PATH = os.path.join(ROOT, 'data', 'interim')
os.makedirs(INTERIM_PATH, exist_ok=True)

def load_raw():
    close, high, low, open_price, volume, market_capitalization, turnover, daily_turnover_rate = load_data()
    return {
        "close": close,
        "high": high,
        "low": low,
        "open_price": open_price,
        "volume": volume,
        "market_capitalization": market_capitalization,
        "turnover": turnover,
        "daily_turnover_rate": daily_turnover_rate
    }

import pandas as pd
import os # 假设你在 load_raw() 或其他地方导入了 os

def align_data(dfs: dict):
    # 统一日期 & 代码：取所有表的交集
    # 注意：这里取的是原始数据的交集，确保所有 df 都有这些日期和代码
    dates = set.intersection(*(set(df.index) for df in dfs.values()))
    codes = set.intersection(*(set(df.columns) for df in dfs.values()))

    dates = sorted(dates)
    codes = sorted(codes)
    cut = 0.5

    # 1. 计算缺失值比例，缺失值超过 cut * datas 长度的 code 直接删除（对所有表同步处理）
    codes_to_drop = set()
    # len(dates) 是所有表日期交集的长度，代表对齐后的行数
    min_data_points = len(dates) 

    for name, df in dfs.items():
        # 筛选出在原始 df 中，缺失值数量超过阈值的代码
        # 筛选的 df 最好是先 reindex 过的，但考虑到效率和原逻辑，使用原始 df 上的 codes
        # 为了保证准确性，我们只对初始 codes 交集中的股票进行检查
        df_to_check = df.reindex(index=dates, columns=codes) # 临时对齐到交集再检查

        # 检查缺失值：缺失值数量 > 0.1 * 对齐后的日期长度
        bad_codes = df_to_check.columns[df_to_check.isnull().sum(axis=0) > cut * min_data_points]
        
        if len(bad_codes) > 0:
            # 修正：将打印信息中的 0.5 替换为 cut 的值
            print(f"{name} 缺失值超过{cut} datas长度的 code（将被全部删除）:")
            print(list(bad_codes))
        codes_to_drop |= set(bad_codes)
    
    # 2. 更新 codes 列表，移除所有被标记删除的代码
    # 这是最终用于对齐的代码列表
    codes = [c for c in codes if c not in codes_to_drop]

    # 3. 移除多余的切片循环 (逻辑错误/冗余)
    # 之前的代码有：
    # for name, df in dfs.items():
    #     dfs[name] = df.loc[:, [c for c in df.columns if c in codes]]
    # 这一步是多余的，因为 reindex 会处理列的对齐和缺失。我们直接进入 reindex 步骤。

    aligned = {}
    for name, df in dfs.items():
        # 使用更新后的 codes 和 dates 列表进行最终对齐
        # reindex 会自动删除不在 codes 中的列，并填充不在 dates 中的行
        df2 = df.reindex(index=dates, columns=codes).sort_index()
        aligned[name] = df2

    # 拼成一个 (date, code) 的长表 panel
    panel = pd.concat(
        [
            # 修改前：aligned["close"].stack().rename("close"),
            # 修改後：加上 dropna=False
            aligned["close"].stack(dropna=False).rename("close"),
            aligned["high"].stack(dropna=False).rename("high"),
            aligned["low"].stack(dropna=False).rename("low"),
            aligned["open_price"].stack(dropna=False).rename("open_price"),
            aligned["volume"].stack(dropna=False).rename("volume"),
            aligned["market_capitalization"].stack(dropna=False).rename("market_capitalization"),
            aligned["turnover"].stack(dropna=False).rename("turnover"),
            aligned["daily_turnover_rate"].stack(dropna=False).rename("daily_turnover_rate"),
        ],
        axis=1
    )
    panel.index.set_names(["date", "code"], inplace=True)
    
    # 4. 移除调试代码
    for code in codes:
         print(code)
    print(len(codes))

    return aligned, panel
if __name__ == "__main__":
    dfs = load_raw()
    aligned_dict, panel = align_data(dfs)

    # 保存对齐后的宽表（每个字段一个 df）
    for name, df in aligned_dict.items():
        df.to_pickle(os.path.join(INTERIM_PATH, f'{name}_aligned.pkl'))

    # 保存长面板（date × code）
    panel.to_pickle(os.path.join(INTERIM_PATH, 'panel_aligned.pkl'))

    print("对齐完成：")
    print(panel.head(20))
   



    #
