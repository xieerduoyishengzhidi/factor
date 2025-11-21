# factor_evaluation/layer_backtest.py
import pandas as pd
import matplotlib.pyplot as plt
import os

class LayerBacktester:
    def __init__(self, cleaned_data, groups=5, factor_name='factor'):
        self.data = cleaned_data.copy()
        self.groups = groups
        self.factor_name = factor_name

    def run(self):
        # 1. 每日分組
        # 使用 qcut 進行等頻分箱，labels=False 得到 0, 1, 2, 3, 4
        def get_group(x):
            try:
                return pd.qcut(x, self.groups, labels=False, duplicates='drop')
            except ValueError:
                return pd.Series(index=x.index, data=-1)

        # self.data['group'] = self.data.groupby(level='date')['factor'].apply(get_group)
        # self.data['group'] = self.data.groupby(level='date', group_keys=False)['factor'].apply(get_group)
        raw_groups = self.data.groupby(level='date')['factor'].apply(get_group)
        self.data['group'] = raw_groups.droplevel(0)
        # 過濾掉無法分組的日子
        valid_grouped = self.data[self.data['group'] != -1]

        # 2. 計算各組平均收益 (等權重)
        # 注意：這裡計算的是單利 (Simple Return)
        layer_ret = valid_grouped.groupby(['date', 'group'])['ret'].mean().unstack()
        
        # 重命名列 Group_1 (因子最小) ~ Group_5 (因子最大)
        layer_ret.columns = [f'G{i+1}' for i in range(self.groups)]
        
        # 3. 計算多空收益 (Top - Bottom)
        layer_ret['Long-Short'] = layer_ret[f'G{self.groups}'] - layer_ret['G1']
        
        return layer_ret

    def plot_cumulative(self, layer_ret, save_path=None):
        # 計算累積收益 (使用單利累加近似，或者複利 (1+r).cumprod())
        # 為了看清楚趨勢，這裡用 log return 的累加比較科學，或者簡單單利累加
        cum_ret = layer_ret.cumsum()

        plt.figure(figsize=(12, 6))
        
        # 畫各組曲線
        for col in layer_ret.columns:
            if col == 'Long-Short': continue
            plt.plot(cum_ret.index, cum_ret[col], label=col, alpha=0.6)

        # 突出顯示多空曲線
        plt.plot(cum_ret.index, cum_ret['Long-Short'], label='Long-Short', color='black', linewidth=2.5)

        plt.title(f"Layered Cumulative Return - {self.factor_name} (Groups={self.groups})")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # 保存图片
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"分层回测图已保存至: {save_path}")
        
        plt.show()