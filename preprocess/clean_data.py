# preprocess/clean_data.py
import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(__file__))    # factor/
INTERIM_PATH = os.path.join(ROOT, 'data', 'interim')
PROCESSED_PATH = os.path.join(ROOT, 'data', 'processed')
os.makedirs(PROCESSED_PATH, exist_ok=True)

def load_panel():
    panel = pd.read_pickle(os.path.join(INTERIM_PATH, 'panel_aligned.pkl'))
    return panel
def add_status_fields(panel: pd.DataFrame) -> pd.DataFrame:
    """
    增加以下辅助字段:
    - suspended: 是否停牌 (成交量为 0 或为 NaN, 1=停牌, 0=未停牌)
    - listed: 是否已上市 (上市首日及之前行情全为NaN, 1=已上市, 0=未上市)
    - limit_up: 是否涨停 (close == high, 且不为NaN)
    - limit_down: 是否跌停 (close == low, 且不为NaN)
    - close_ffill: 前向填充后的收盘价 (仅画图/资产估算用，严禁用于收益等)
    - pct_chg: 当日涨跌幅 (close/昨收-1)
    - ret_1d: 当日真实收益，考虑除权、停牌，若停牌即为NaN
    - ret_fwd_1d: 前瞻1日真实收益
    - ret_fwd_5d: 前瞻5日真实收益（简单价格/停牌逻辑）

    如果算出来nan就设nan~
    """
    df = panel.copy()

    # 1. 增加辅助状态字段
    # === suspended ===
    df['suspended'] = np.where((df['volume'] == 0) | (df['volume'].isna()), 1, 0)
    df['suspended'] = df['suspended'].astype(float)  # 保持 nan 能传递

    # === listed ===
    # 只要所有行情都是NaN就认为未上市，实现上以 'close' 字段为准
    # 只要该code首次出现不为NaN就认为上市，前面时间全部设为0
    # 取 code 分组的第一个非NaN出现日期；之后全为1，否则为0
    def compute_listed_flag(code_df):
        is_listed = code_df['close'].notna().cumsum() > 0
        return is_listed.astype(float)
    df['listed'] = (
        df.groupby('code', group_keys=False)
        .apply(compute_listed_flag)
    )
    # 由于 pandas apply特性 index不变，直接生成

    # === limit_up, limit_down ===
    # 注意只在当天数据非NaN时计算，否则为NaN
    df['limit_up'] = np.where(
        (df['close'].notna()) & (df['high'].notna()) & (df['close'] == df['high']),
        1, np.where(df['close'].isna() | df['high'].isna(), np.nan, 0)
    )
    df['limit_down'] = np.where(
        (df['close'].notna()) & (df['low'].notna()) & (df['close'] == df['low']),
        1, np.where(df['close'].isna() | df['low'].isna(), np.nan, 0)
    )

    # 前向 close，只用于画图/资产估算
    df['close_ffill'] = (
        df.groupby('code', group_keys=False)['close']
        .apply(lambda x: x.ffill())
    )

    # pct_chg: 优先当日涨跌幅
    def compute_pct_chg(group):
        close = group['close']
        fill_close = group.get('close_ffill', None)
        prev_close = close.shift(1)
        pct_chg = close / prev_close - 1

        # 找到：本日不为nan，昨日为nan的位置，且已上市，且未停牌
        mask = close.notna() & prev_close.isna()&(group['listed'] == 1)&(group['suspended'] == 0)
        if fill_close is not None:
            prev_fill_close = fill_close.shift(1)
            pct_chg[mask] = (close[mask] / prev_fill_close[mask] - 1).values
        return pct_chg

    df['pct_chg'] = (
        df.groupby('code', group_keys=False)
        .apply(compute_pct_chg)
    )

    # 停牌/未上市日无返回
    df.loc[df['listed'] == 0, 'pct_chg'] = np.nan
    df.loc[df['suspended'] == 1, 'pct_chg'] = np.nan

    # === 收益相关 ===
    # ret_1d: close/昨收-1，停牌或未上市日为NaN
    df['ret_1d'] = df['pct_chg']
    # 若停牌，收益设为nan
    df.loc[df['suspended'] == 1, 'ret_1d'] = np.nan
    df.loc[df['listed'] == 0, 'ret_1d'] = np.nan

    # ret_fwd_1d: 明日close/今日close-1，但需考虑次日是否有价格、是否停牌
    def calc_ret_fwd_1d(group: pd.DataFrame):
        s = group['close']
        fwd = s.shift(-1) / s - 1
        # 若今或次日停牌或未上市，设nan
        fwd[(group['listed'] == 0) | (group['listed'].shift(-1) == 0)] = np.nan
        fwd[(group['suspended'] == 1) | (group['suspended'].shift(-1) == 1)] = np.nan
        return fwd

    df['ret_fwd_1d'] = (
        df.groupby('code', group_keys=False)
        .apply(calc_ret_fwd_1d)
    )

    # ret_fwd_5d: 未来五日收益率，简单 close_{t+5}/close_{t}-1, 同理过滤
    def calc_ret_fwd_5d(group: pd.DataFrame):
        s = group['close']
        fwd = s.shift(-5) / s - 1
        # 只要未来5天内有一天未上市或停牌，都设nan
        for i in range(1, 6):
            mask = (group['listed'].shift(-i) == 0) | (group['suspended'].shift(-i) == 1)
            fwd[mask] = np.nan
        # 本日未上市/停牌也要设nan
        fwd[(group['listed'] == 0) | (group['suspended'] == 1)] = np.nan
        return fwd

    df['ret_fwd_5d'] = (
        df.groupby('code', group_keys=False)
        .apply(calc_ret_fwd_5d)
    )

    return df


if __name__ == "__main__":
     panel = load_panel()
     print(panel.head(100))
     print(panel.info())
     print(panel.isnull().sum())
     panel = add_status_fields(panel)
     panel.to_pickle(os.path.join(PROCESSED_PATH, 'panel_cleaned.pkl'))
     print(panel.head(100))
     print(panel.info())
     print(panel.isnull().sum())
