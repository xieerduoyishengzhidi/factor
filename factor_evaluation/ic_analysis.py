# factor_evaluation/ic_analysis.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class ICAnalyzer:
    def __init__(self, cleaned_data):
        self.data = cleaned_data

    def calculate_daily_ic(self, method='spearman', min_stocks=10):
        """
        計算每日 IC 序列
        min_stocks: 當天有效股票少於此數則不計算 (避免早期數據噪音)
        """
        def _calc(group):
            if len(group) < min_stocks:
                return np.nan
            return group['factor'].corr(group['ret'], method=method)

        self.ic_series = self.data.groupby(level='date').apply(_calc)
        return self.ic_series

    def get_summary(self):
        if not hasattr(self, 'ic_series'):
            self.calculate_daily_ic()
            
        ic_mean = self.ic_series.mean()
        ic_std = self.ic_series.std()
        ic_ir = ic_mean / ic_std if ic_std != 0 else 0
        
        # 勝率 (IC > 0 的日子佔比)
        win_rate = (self.ic_series > 0).sum() / self.ic_series.count()

        return pd.Series({
            "IC Mean": ic_mean,
            "IC Std": ic_std,
            "ICIR": ic_ir,
            "Win Rate (>0)": win_rate,
            "Valid Days": self.ic_series.count()
        })

    def plot_ic(self):
        if not hasattr(self, 'ic_series'):
            self.calculate_daily_ic()
            
        plt.figure(figsize=(12, 5))
        # 畫柱狀圖
        self.ic_series.plot(kind='bar', color='skyblue', alpha=0.6, label='Daily IC')
        
        # 畫均線
        ma_ic = self.ic_series.rolling(window=20).mean()
        plt.plot(ma_ic.index, ma_ic.values, color='orange', label='20D MA')
        
        plt.axhline(self.ic_series.mean(), color='red', linestyle='--', label=f'Mean: {self.ic_series.mean():.3f}')
        plt.title("Factor Rank IC Series")
        
        # 因為 X 軸是日期，bar圖標籤會太密，簡化顯示
        ax = plt.gca()
        ax.xaxis.set_major_locator(plt.MaxNLocator(10)) 
        
        plt.legend()
        plt.grid(axis='y', linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.show()