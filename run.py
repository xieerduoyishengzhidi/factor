# run_evaluation.py
import os
import pandas as pd
import warnings

# 導入自定義模塊 (確保 factor_evaluation 文件夾裡有 __init__.py，或者為空文件)
from factor_evaluation.util import get_clean_factor_and_forward_returns
from factor_evaluation.ic_analysis import ICAnalyzer
from factor_evaluation.layer_backtest import LayerBacktester

# 忽略一些 pandas 的 FutureWarning
warnings.simplefilter(action='ignore', category=FutureWarning)

# === 參數設置 ===
PANEL_PATH = os.path.join('data', 'processed', 'panel_cleaned.pkl')
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--factor_name', type=str, default='illiq_guiji', help='因子名称, 用于自动设定path')
args, unknown = parser.parse_known_args()
FACTOR_NAME = args.factor_name
FACTOR_PATH = os.path.join('data', 'factors', f'{FACTOR_NAME}.pkl')

def main():
    # 1. 讀取數據
    print(f"正在讀取 Panel 數據: {PANEL_PATH}")
    if not os.path.exists(PANEL_PATH):
        print("錯誤：找不到 Panel 文件，請先運行 clean_data.py")
        return
    panel = pd.read_pickle(PANEL_PATH)

    print(f"正在讀取 因子 數據: {FACTOR_PATH}")
    if not os.path.exists(FACTOR_PATH):
        print("錯誤：找不到因子文件，請先運行因子計算腳本")
        return
    factor = pd.read_pickle(FACTOR_PATH)
    factor=factor.set_index(['date', 'code'])
    # 2. 數據融合與清洗
    print("\n[1/3] 正在合併因子與未來收益...")
    # 使用 ret_fwd_1d (T+1收益) 進行評估
    merged_data = get_clean_factor_and_forward_returns(
        factor, panel, factor_name=FACTOR_NAME, fwd_ret_col='ret_fwd_1d'
    )
    print(f"有效樣本數: {len(merged_data)}")
    print(merged_data.head())
    
    # 3. IC 分析
    print("\n[2/3] 正在進行 IC 分析...")
    ic_analyzer = ICAnalyzer(merged_data, factor_name=FACTOR_NAME)
    
    # 計算並打印統計結果
    ic_stats = ic_analyzer.get_summary()
    print("-" * 30)
    print("IC 績效指標:")
    print(ic_stats)
    print("-" * 30)
    
    # 保存图片路径
    results_dir = os.path.join('data', 'results')
    os.makedirs(results_dir, exist_ok=True)
    ic_plot_path = os.path.join(results_dir, f'{FACTOR_NAME}_ic_analysis.png')
    
    # 畫圖
    ic_analyzer.plot_ic(save_path=ic_plot_path) 
   

    # 4. 分層回測
    print("\n[3/3] 正在進行分層回測 (N=5)...")
    layer_tester = LayerBacktester(merged_data, groups=5, factor_name=FACTOR_NAME)
    layer_ret = layer_tester.run()
    
    # 打印各組年化收益 (簡單估算)
    print("各組年化收益率 (近似值):")
    print(layer_ret.mean() * 252)

    # 保存图片路径
    layer_plot_path = os.path.join(results_dir, f'{FACTOR_NAME}_layer_backtest.png')
    
    # 畫圖
    layer_tester.plot_cumulative(layer_ret, save_path=layer_plot_path)
    
    print("\n分析完成！")

if __name__ == "__main__":
    main()