import os
from tkinter import N
import pandas as pd

# 使用 os.path.join
def load_data():
    datapath = os.path.join(os.path.dirname(__file__), '../data/raw/')
    
    close = pd.read_pickle(os.path.join(datapath,'CLOSE.pkl'))
    high = pd.read_pickle(os.path.join(datapath,'HIGH.pkl'))
    low = pd.read_pickle(os.path.join(datapath,'LOW.pkl'))
    open_price = pd.read_pickle(os.path.join(datapath,'OPEN.pkl'))
    volume = pd.read_pickle(os.path.join(datapath,'VOLUME.pkl'))
    market_capitalization = pd.read_pickle(os.path.join(datapath,'market_cap.pkl'))
    #print(market_capitalization.head())     # 打印market_capitalization的前20行
    turnover = pd.read_pickle(os.path.join(datapath,'TURNOVER.pkl'))
    daily_turnover_rate = pd.read_pickle(os.path.join(datapath,'DAILY_TURNOVER_RATE.pkl'))
    
    return close, high, low, open_price, volume, market_capitalization, turnover, daily_turnover_rate

if __name__ == "__main__":
    close, high, low, open_price, volume, market_capitalization, turnover, daily_turnover_rate = load_data()
    print(close.head())
    print(high.head())
    print(low.head())
    print(open_price.head())
    print(volume.head())
    print(market_capitalization.head())
    print(turnover.head())
    print(daily_turnover_rate.head())
   
    """
    print("close.info()")
    print(high.info())
    print(low.info())
    print(open_price.info())
    print(volume.info())
    print(market_capitalization.info())
    print(turnover.info())
    print(daily_turnover_rate.info())

    print(close.isnull().sum())
    print(high.isnull().sum())
    print(low.isnull().sum())
    print(open_price.isnull().sum())
    print(volume.isnull().sum())
    print(market_capitalization.isnull().sum())
    print(turnover.isnull().sum())
    print(daily_turnover_rate.isnull().sum())
    """

    # 对同一个column，检查close和high,low,open_price,volume,market_capitalization,turnover,daily_turnover_rate是否同时存在缺失值
    # 检查每个col是否在所有DataFrame中都缺失，或者都不缺失，否则报错
    
    dataframes = {
        "close": close,
        "high": high,
        "low": low,
        "open_price": open_price,
        "volume": volume,
        "market_capitalization": market_capitalization,
        "turnover": turnover,
        "daily_turnover_rate": daily_turnover_rate
    }

    # 所有出现过的列
    all_columns = set()
    for df in dataframes.values():
        all_columns |= set(df.columns)

    # 记录每列的缺失数量
    missing_summary = {}

    for col in all_columns:
        col_missing_info = {}  # 每个 df 中 col 的缺失情况

        is_missing_list = []

        for name, df in dataframes.items():
            if col not in df.columns:
                col_missing_info[name] = "不存在"
                is_missing_list.append(True)  # 当作全缺失处理
            else:
                missing_count = df[col].isna().sum()
                col_missing_info[name] = missing_count
                is_missing_list.append(missing_count == len(df))

        missing_summary[col] = col_missing_info

        # 判断缺失情况是否一致
        if all(is_missing_list):
            print(f"列 {col} 在所有表中都完全缺失")
        elif not any(is_missing_list):
            print(f"列 {col} 在所有表中都存在（无全缺失情况）")
        else:
            print(f"⚠ 列 {col} 缺失情况不一致：")
            for name, info in col_missing_info.items():
                print(f" - {name}: {info}")
            print("请检查该列！\n")

    # 打印汇总表
    #print("\n===== 缺失统计汇总 =====")
    #print(pd.DataFrame(missing_summary).T)
    
    
    print(len(close.index))
    #print(market_capitalization.head(20))

