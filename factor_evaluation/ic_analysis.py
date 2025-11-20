# factor_evaluation/ic_analysis.py
import pandas as pd
import numpy as np

class ICAnalyzer:
    def __init__(self, merged_data):
        """
        merged_data: 包含 'factor' 和 'ret_1d' 兩列的 DataFrame，索引為 (date, code)
        """
        self.data = merged_data

    def calculate_ic(self, method='spearman'):
        """
        計算每日 IC
        method: 'spearman' (RankIC, 推薦) 或 'pearson' (Normal IC)
        """
        # 按日期分組，計算因子和收益的相關性
        ic_series = self.data.groupby(level='date').apply(
            lambda x: x['factor'].corr(x['ret'], method=method)
        )
        return ic_series

    def analyze(self):
        ic_series = self.calculate_ic()
        
        # 計算統計指標
        ic_mean = ic_series.mean()
        ic_std = ic_series.std()
        ic_ir = ic_mean / ic_std if ic_std != 0 else 0  # 信息比率
        positive_ratio = (ic_series > 0).sum() / len(ic_series) # 正 IC 佔比
        
        stats = {
            "IC Mean": ic_mean,
            "IC Std": ic_std,
            "ICIR": ic_ir,
            "Positive Ratio": positive_ratio
        }
        
        return ic_series, stats