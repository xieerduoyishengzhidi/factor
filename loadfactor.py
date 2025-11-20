import pandas as pd
import numpy as np
import os
from factors.base_factor import get_factor
import factors.illiq_guiji 
# 1. Create Mock Data
root=os.path.dirname(os.path.abspath(__file__))
data_path=os.path.join(root, 'data', 'processed', 'panel_cleaned.pkl')
factor_path=os.path.join(root, 'data', 'factors', 'illiq_guiji.parquet')
df = pd.read_pickle(data_path)

dates = pd.unique(df.index.get_level_values('date'))
assets = pd.unique(df.index.get_level_values('code'))
# 创建 MultiIndex 并重新索引
new_index = pd.MultiIndex.from_product([dates, assets], names=['date', 'code'])
df = df.reindex(new_index)

# 2. Instantiate the Factor
# notice: we use the name defined in @register_factor
factor = get_factor("illiq_guiji", lookback=20)

# 3. Run
result = factor.run(df)


print("Factor Calculation Successful!")
print(result.head(100))
print(result.tail(100))
print(result.info())

# 保存结果，优先使用 parquet，如果不可用则使用 pickle
try:
    result.reset_index().to_parquet(factor_path)
    print(f"Factor saved to {factor_path} (parquet format)")
except ImportError:
    # 如果 parquet 不可用，使用 pickle
    pickle_path = factor_path.replace('.parquet', '.pkl')
    result.reset_index().to_pickle(pickle_path)
    print(f"Factor saved to {pickle_path} (pickle format, parquet not available)")