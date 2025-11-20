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
        公式: sum(log(1 + |ret|)) / sum(volume) over lookback window
        """
        # 确保索引是 MultiIndex
        if not isinstance(panel.index, pd.MultiIndex):
            raise ValueError("panel must have MultiIndex (date, code)")
        
        # 获取索引层级名称
        index_names = panel.index.names
        date_level = 0
        code_level = 1
        
        # 计算每日收益率绝对值
        daily_term = np.log(1 + panel['close'].groupby(level=code_level).pct_change(fill_method=None).abs())
        
        # 计算 rolling log-sum（按 code 分组，滚动求和）
        logsum = daily_term.groupby(level=code_level).rolling(window=self.lookback, min_periods=1).sum()
        logsum = logsum.droplevel(0) if logsum.index.nlevels > 2 else logsum
        
        # 计算 rolling volume sum（按 code 分组，滚动求和）
        amountsum = panel['volume'].groupby(level=code_level).rolling(window=self.lookback, min_periods=1).sum()
        amountsum = amountsum.droplevel(0) if amountsum.index.nlevels > 2 else amountsum
        
        # 计算因子值：logsum / amountsum
        # 避免除零，将 0 替换为 NaN
        result = logsum / amountsum.replace(0, np.nan)
        
        # 确保索引对齐
        result = result.reindex(panel.index)
        
        # 返回 Series，索引与 panel 对齐
        return result








