import pandas as pd
def merge_factor_and_forward_return(factor_df, panel_df, factor_name, fwd_ret_col='ret_fwd_1d'):
    """
    將因子值與面板數據中的「未來收益率」合併
    """
    # 1. 取出未来收益率
    next_ret_1d = panel_df['ret_fwd_1d']
    
    # 2. 確保因子也是 Series
    if isinstance(factor_df, pd.DataFrame):
        factor = factor_df[factor_name]
    else:
        factor = factor_df
        
    # 3. 合併 (依靠索引 date, code 自動對齊)
    merged = pd.concat([factor, next_ret_1d], axis=1)
    merged.columns = ['factor', 'ret_1d']
    
    # 4. 去除空值 (因子為空或收益為空都無法分析)
    merged = merged.dropna()
    
    return merged