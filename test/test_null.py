import os 
import pandas as pd
import pickle

factor_path=os.path.join(os.path.dirname(__file__), 'data', 'factors', 'illiq_guiji.pkl')
factor = pd.read_pickle(factor_path)
factor=factor.set_index(['date', 'code'])
print(factor.index)


# 找每个code第一次不是nan的date并打印
# 修正：此处原代码假定 'factor' 列存在，但你的 DataFrame 结构是 MultiIndex ['date', 'code']，内容即是因子值本身（Series 或 DataFrame），需根据实际结构区分
if isinstance(factor, pd.Series):
    # 如果为 Series，直接找每个 code 第一次非空 date
    first_valid_dates = factor.groupby('code').apply(lambda x: x.first_valid_index()[0] if x.first_valid_index() is not None else None)
else:
    # 如果为 DataFrame，且有一个具体的因子列名（如 'factor'），需指定列
    if 'factor' in factor.columns:
        first_valid_dates = factor['factor'].groupby('code').apply(lambda x: x.first_valid_index()[0] if x.first_valid_index() is not None else None)
    else:
        # 如没有 factor 列，取第一个数值列
        value_col = factor.columns[0]
        first_valid_dates = factor[value_col].groupby('code').apply(lambda x: x.first_valid_index()[0] if x.first_valid_index() is not None else None)

print(first_valid_dates)

# 统计每个 code 的 nan 天数（假设每个 code 每天只有一个因子值）
nan_days = factor.isna().groupby(level='code').sum()
print(nan_days)



# 检查原始的 close 价格
# 您可能需要重新加载 panel 数据来查看：
# panel = pd.read_pickle(PANEL_PATH)
# print(panel.xs(code_sample, level='code')['close'].head(25))
print(factor.head(25))
print(factor.info())