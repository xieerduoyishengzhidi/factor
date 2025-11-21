# factors/panic_factor.py

# 1. Import the tools from your base file
from factors.base_factor import BaseFactor, register_factor

import pandas as pd
import numpy as np

# 2. Use the decorator to give it a name for the registry
@register_factor("panic_factor") 
class PanicFactor(BaseFactor):
    
    # Optional: Override __init__ if you want to set default defaults
    def __init__(self, lookback=21, weight_method='equal', **kwargs):
        # Pass arguments back to the parent (BaseFactor)
        super().__init__(name="panic_factor", lookback=lookback, **kwargs)
        self.weight_method = weight_method  # 'equal' 等权, 'market_cap' 流通市值权重, 'turnover' 成交额权重

    # 3. Implement the REQUIRED calculate method
   
    def calculate(self, panel: pd.DataFrame) -> pd.Series:
        """
        计算惊恐因子（Panic Factor）
        
        步骤：
        1. 计算市场收益 r_m,t = (1/N_t) * Σ r_i,t (等权) 或加权
        2. 计算惊恐度 panic_i,t = |r_i,t - r_m,t| / (|r_i,t| + |r_m,t| + 0.1)
        3. 计算惊恐收益 x_i,t = panic_i,t * r_i,t
        4. 计算因子值 factor_i,t = StdDev(x_i,t-20, ..., x_i,t) (21日标准差)
        
        保证 result 与 panel 的 index 完全对齐，均为 MultiIndex ('date', 'code')
        """
        # 1. 检查 panel 是否为 MultiIndex，且 index 顺序为 ('date', 'code')
        if not isinstance(panel.index, pd.MultiIndex) or panel.index.names != ['date', 'code']:
            raise ValueError("panel 必须是 MultiIndex, 且 index 顺序为 ('date', 'code')")

        lookback = self.lookback
        min_p = lookback // 2  # 放宽 min_periods 条件
        
        # 2. 计算个股日收益率 r_i,t
        # 按 code 分组计算收益率，避免跨股票计算
        r_i = panel['close'].groupby('code').pct_change(fill_method=None)
        
        # 3. 计算市场收益 r_m,t
        # 按日期分组，计算每日的市场收益
        r_m = self._calculate_market_return(panel, r_i)
        
        # 4. 计算惊恐度 panic_i,t = |r_i,t - r_m,t| / (|r_i,t| + |r_m,t| + 0.1)
        r_i_abs = r_i.abs()
        r_m_abs = r_m.abs()
        panic = (r_i - r_m).abs() / (r_i_abs + r_m_abs + 0.1)
        
        # 5. 计算惊恐收益 x_i,t = panic_i,t * r_i,t
        x_i = panic * r_i
        
        # 6. 计算因子值：21日滚动标准差
        # 按 code 分组，计算滚动标准差
        result = x_i.groupby('code').rolling(
            window=lookback,
            min_periods=min_p
        ).std()
        
        # --- 步骤 B: 核心索引對齊邏輯 (解決 (code, date) vs (date, code) 問題) ---
        
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
    
    def _calculate_market_return(self, panel: pd.DataFrame, r_i: pd.Series) -> pd.Series:
        """
        计算市场收益 r_m,t
        
        参数:
            panel: MultiIndex DataFrame, index=['date', 'code']
            r_i: 个股收益率 Series, index=['date', 'code']
        
        返回:
            r_m: 市场收益率 Series, index=['date', 'code']，每个日期所有股票的值相同
        """
        if self.weight_method == 'equal':
            # 等权：r_m,t = (1/N_t) * Σ r_i,t
            # 按日期分组，计算等权平均（自动忽略 NaN）
            # 将每个日期的市场收益广播到该日期的所有股票
            r_m = r_i.groupby('date').transform('mean')
        elif self.weight_method == 'market_cap':
            # 流通市值加权
            if 'market_capitalization' not in panel.columns:
                raise ValueError("使用市值加权需要 panel 中包含 'market_capitalization' 列")
            market_cap = panel['market_capitalization']
            # 先计算每个日期的市场收益（只考虑有效数据）
            r_m_by_date = {}
            for date, date_group in r_i.groupby('date'):
                valid_mask = date_group.notna() & market_cap.loc[date].notna()
                if valid_mask.sum() == 0:
                    r_m_by_date[date] = np.nan
                else:
                    weights = market_cap.loc[date, valid_mask] / market_cap.loc[date, valid_mask].sum()
                    r_m_by_date[date] = (date_group[valid_mask] * weights).sum()
            # 将每个日期的市场收益广播到该日期的所有股票
            r_m = r_i.groupby('date').transform(lambda x: r_m_by_date.get(x.name, np.nan))
        elif self.weight_method == 'turnover':
            # 成交额加权
            if 'turnover' not in panel.columns:
                raise ValueError("使用成交额加权需要 panel 中包含 'turnover' 列")
            turnover = panel['turnover']
            # 先计算每个日期的市场收益（只考虑有效数据）
            r_m_by_date = {}
            for date, date_group in r_i.groupby('date'):
                valid_mask = date_group.notna() & turnover.loc[date].notna()
                if valid_mask.sum() == 0:
                    r_m_by_date[date] = np.nan
                else:
                    weights = turnover.loc[date, valid_mask] / turnover.loc[date, valid_mask].sum()
                    r_m_by_date[date] = (date_group[valid_mask] * weights).sum()
            # 将每个日期的市场收益广播到该日期的所有股票
            r_m = r_i.groupby('date').transform(lambda x: r_m_by_date.get(x.name, np.nan))
        else:
            raise ValueError(f"不支持的权重方法: {self.weight_method}")
        
        return r_m

