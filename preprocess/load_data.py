import os
from tkinter import N
import pandas as pd

# 使用 os.path.join
datapath = os.path.join(os.path.dirname(__file__), '../data/raw/')

close = pd.read_pickle(os.path.join(datapath,'CLOSE.pkl'))
high = pd.read_pickle(os.path.join(datapath,'HIGH.pkl'))
low = pd.read_pickle(os.path.join(datapath,'LOW.pkl'))
open_price = pd.read_pickle(os.path.join(datapath,'OPEN.pkl'))
volume = pd.read_pickle(os.path.join(datapath,'VOLUME.pkl'))
market_capitalization = pd.read_pickle(os.path.join(datapath,'market_cap.pkl'))
turnover = pd.read_pickle(os.path.join(datapath,'TURNOVER.pkl'))
daily_turnover_rate = pd.read_pickle(os.path.join(datapath,'DAILY_TURNOVER_RATE.pkl'))

if __name__ == "__main__":
   
   """  print(close.info())
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
    print(daily_turnover_rate.isnull().sum()) """

# 对同一个column，检查close和high,low,open_price,volume,market_capitalization,turnover,daily_turnover_rate是否同时存在缺失值
# 检查每个col是否在所有DataFrame中都缺失，或者都不缺失，否则报错
dataframes = [
    close,
    high,
    low,
    open_price,
    volume,
    market_capitalization,
    turnover,
    daily_turnover_rate
]

for col in close.columns:
    # 检查所有表中，该col是否都完全缺失
    is_missing = []
    for df in dataframes:
        # 如果df没有该col，认为该col全缺失
        if col not in df.columns:
            is_missing.append(True)
        else:
            # 判断该列是否全是NA
            is_missing.append(df[col].isnull().all())
    # 如果is_missing全True或全False，认为一致，否则报列名及具体情况
    if all(is_missing) or not any(is_missing):
        print(f"列 {col} 在所有数据表中都缺失")
        continue
    else:
        print(f"列 {col} 在数据表中的缺失情况不一致：")
        for df, miss in zip(
            [
                "close", "high", "low", "open_price",
                "volume", "market_capitalization", "turnover", "daily_turnover_rate"
            ], is_missing
        ):
            print(f" - {df}: {'全缺失' if miss else '有数据'}")
        print("请检查该列！")








