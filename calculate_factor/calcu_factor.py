# main.py
# 调用惊恐因子并保存结果
import pandas as pd
import numpy as np
import os
from factors.base_factor import get_factor
import factors.panic_factor  # 导入因子模块以注册因子

from load_data import load_panel_data

def main():
    # 1. 加载 panel 数据
    print("=" * 60)
    print("开始计算惊恐因子 (Panic Factor)")
    print("=" * 60)
    
    panel = load_panel_data()
    
    # 确保索引格式正确
    dates = pd.unique(panel.index.get_level_values('date'))
    assets = pd.unique(panel.index.get_level_values('code'))
    
    # 创建完整的 MultiIndex 并重新索引（确保所有日期-股票组合都存在）
    new_index = pd.MultiIndex.from_product([dates, assets], names=['date', 'code'])
    panel = panel.reindex(new_index)
    
    # 2. 实例化因子
    # 注意：使用 @register_factor 中定义的名称
    # 参数说明：
    #   lookback: 滚动窗口大小，默认21天（对应21日标准差）
    #   weight_method: 市场收益计算方式，'equal'（等权）、'market_cap'（市值加权）、'turnover'（成交额加权）
    factor = get_factor("panic_factor", lookback=21, weight_method='equal')
    
    print(f"\n因子参数:")
    print(f"  - 名称: {factor.name}")
    print(f"  - 回看窗口: {factor.lookback} 天")
    print(f"  - 权重方法: {factor.weight_method}")
    
    # 3. 运行因子计算
    print("\n开始计算因子...")
    result = factor.run(panel)
    
    print("\n因子计算完成！")
    print(f"结果形状: {result.shape}")
    print(f"结果列: {list(result.columns)}")
    print("\n结果预览（前20行）:")
    print(result.head(20))
    print("\n结果预览（后20行）:")
    print(result.tail(20))
    print("\n结果统计信息:")
    print(result.info())
    print("\n因子值统计:")
    print(result[factor.name].describe())
    
    # 4. 保存结果
    root = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(root, 'data', 'factors'), exist_ok=True)
    factor_path = os.path.join(root, 'data', 'factors', 'panic_factor.pkl')
    
    # 保存为 pickle 格式
    result.reset_index().to_pickle(factor_path)
    print(f"\n因子已保存至: {factor_path}")
    
    # 尝试保存为 parquet 格式（如果可用）
    try:
        parquet_path = factor_path.replace('.pkl', '.parquet')
        result.reset_index().to_parquet(parquet_path)
        print(f"因子已保存至: {parquet_path} (parquet 格式)")
    except ImportError:
        print("注意: parquet 格式不可用，仅保存为 pickle 格式")
    except Exception as e:
        print(f"注意: 保存 parquet 格式时出错: {e}")
    
    print("\n" + "=" * 60)
    print("惊恐因子计算完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()

