# factors/illiq_guiji.py

# 1. Import the tools from your base file
from factors.base_factor import BaseFactor, register_factor

import pandas as pd
import numpy as np

# 2. Use the decorator to give it a name for the registry
@register_factor("illiq_guiji") 
class IlliqGuijiFactor(BaseFactor):
    
    # Optional: Override __init__ if you want to set default defaults
    def __init__(self, lookback=20, **kwargs):
        # Pass arguments back to the parent (BaseFactor)
        super().__init__(name="illiq_guiji", lookback=lookback, **kwargs)

    # 3. Implement the REQUIRED calculate method
   
    def calculate(self, panel: pd.DataFrame) -> pd.Series:
        """
        计算 Illiq Guiji 因子（非流动性因子）
        公式: sum(log(1 + |ret|)) / sum(amount) over lookback window
        保证 result 与 panel 的 index 完全对齐，均为 MultiIndex ('date', 'code')
        """
        # 1. 检查 panel 是否为 MultiIndex，且 index 顺序为 ('date', 'code')
        if not isinstance(panel.index, pd.MultiIndex) or panel.index.names != ['date', 'code']:
            raise ValueError("panel 必须是 MultiIndex, 且 index 顺序为 ('date', 'code')")

        lookback = self.lookback
        # 放宽 min_periods 条件，避免历史初期数据丢失
        min_p = lookback // 2  

        # 2. 先 groupby 'code'，计算每日绝对收益 (daily_term)
        daily_ret_abs = panel['close'].groupby('code').pct_change(fill_method=None).abs()
        daily_term = np.log(1 + daily_ret_abs)

        # 3. 确定分母 (target_vol)：优先使用 turnover
        if 'turnover' in panel.columns:
            target_vol = panel['turnover']
        elif 'volume' in panel.columns:
            target_vol = panel['volume']
        else:
            raise ValueError("panel 中必须有 'turnover' 或 'volume' 列")

        # --- 步驟 A: 滾動求和 (確保 groupby 後 rolling 不跨股票) ---
        
        # 4. 分子滾動求和 (logsum)
        logsum = daily_term.groupby('code').rolling(
            window=lookback, 
            min_periods=min_p
        ).sum()
        
        # 5. 分母滾動求和 (amountsum)
        amountsum = target_vol.groupby('code').rolling(
            window=lookback, 
            min_periods=min_p
        ).sum()

        # 6. 計算結果
        result = logsum / amountsum.replace(0, np.nan)

        # --- 步驟 B: 核心索引對齊邏輯 (解決 (code, date) vs (date, code) 問題) ---
        
        # 7. 如果索引層級 > 2，則假設最外層是冗餘的分組鍵並將其移除
        if result.index.nlevels > 2:
            result = result.droplevel(level=0)
            
        # 8. 確保索引名稱存在並與 panel 一致
        if result.index.nlevels == 2 and result.index.names != panel.index.names:
            # 複製 panel 的 index name，以便後續判斷
            result.index.set_names(panel.index.names, inplace=True)
            
        # 9. 檢查並修正索引順序：如果當前是 ['code', 'date'] 而目標是 ['date', 'code']，則交換
        if result.index.names[0] == panel.index.names[1] and result.index.names[1] == panel.index.names[0]:
            result = result.swaplevel('date', 'code')

        # 10. 排序和最終對齊 (reindex)
        result = result.sort_index()
        result = result.reindex(panel.index)

        # 11. 最終清理：若當天無收盤價（如停牌），該值設為 NaN
        mask_no_close = panel['close'].isna()
        result[mask_no_close] = np.nan

        return result





