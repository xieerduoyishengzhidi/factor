# load_data.py
# 用于加载惊恐因子所需的数据
import os
import pandas as pd

def load_panel_data():
    """
    加载处理后的 panel 数据
    
    返回:
        panel: MultiIndex DataFrame, index=['date', 'code']
               包含 close, high, low, open_price, volume, 
               market_capitalization, turnover 等列
    """
    root = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(root, 'data', 'processed', 'panel_cleaned.pkl')
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"找不到 panel 数据文件: {data_path}\n请先运行数据预处理脚本")
    
    panel = pd.read_pickle(data_path)
    
    # 确保索引格式正确
    if not isinstance(panel.index, pd.MultiIndex):
        if {'date', 'code'}.issubset(panel.columns):
            panel = panel.set_index(['date', 'code'])
        else:
            raise ValueError("panel 必须是 MultiIndex 或含有 'date', 'code' 列")
    
    # 确保索引名称正确
    if panel.index.names != ['date', 'code']:
        panel.index.set_names(['date', 'code'], inplace=True)
    
    # 确保索引顺序正确（date 在外层，code 在内层）
    if panel.index.names[0] != 'date':
        panel = panel.swaplevel('date', 'code')
    
    # 排序
    panel = panel.sort_index()
    
    print(f"成功加载 panel 数据:")
    print(f"  - 形状: {panel.shape}")
    print(f"  - 日期范围: {panel.index.get_level_values('date').min()} 至 {panel.index.get_level_values('date').max()}")
    print(f"  - 股票数量: {len(panel.index.get_level_values('code').unique())}")
    print(f"  - 列: {list(panel.columns)}")
    
    return panel

if __name__ == "__main__":
    panel = load_panel_data()
    print("\n数据预览:")
    print(panel.head(20))

