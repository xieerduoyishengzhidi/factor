""" import os 
import pandas as pd
def standardize(factor_df):
    factor_name=factor_df.name
    factor_path=os.path.join(os.path.dirname(__file__), 'data', 'factors', f'{factor_name}.pkl')
    factor_df = pd.read_pickle(factor_path)
    factor_df['factor_norm'] = factor_df.groupby('date')[factor_name].transform(lambda x: (x - x.mean()) / x.std())
    factor_norm_path=os.path.join(os.path.dirname(__file__), 'data', 'factors', f'{factor_name}_norm.pkl')
    factor_df.to_pickle(factor_norm_path)
    return factor_norm_path
standardize('illiq_guiji') """