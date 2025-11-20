# factor_evaluation/utils.py
import pandas as pd

def get_clean_factor_and_forward_returns(factor_df, panel_df, factor_name='illiq_guiji', fwd_ret_col='ret_fwd_1d'):
    """
    合併因子值與未來收益率，並去除空值
    """
    # 1. 提取因子列 (兼容 Series 和 DataFrame)
    if isinstance(factor_df, pd.Series):
        factor = factor_df.rename('factor')
    else:
        # 如果是 DataFrame，嘗試找對應列名，找不到就取第一列
        if factor_name in factor_df.columns:
            factor = factor_df[factor_name].rename('factor')
        else:
            factor = factor_df.iloc[:, 0].rename('factor')

    # 2. 提取收益率列
    if fwd_ret_col not in panel_df.columns:
        raise ValueError(f"Panel 中找不到列: {fwd_ret_col}")
    ret = panel_df[fwd_ret_col].rename('ret')

    # 3. 合併 (自動按 date, code 索引對齊)
    merged = pd.concat([factor, ret], axis=1)

    # 4. 清洗數據
    # 去除因子為 NaN 或 收益為 NaN 的行 (未上市、停牌、數據不足)
    cleaned = merged.dropna()
    
    return cleaned