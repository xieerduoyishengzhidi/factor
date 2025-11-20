# factors/base.py
import abc
import numpy as np
import pandas as pd

# =========================
# 因子注册器（方便通过名字创建因子）
# =========================
FACTOR_REGISTRY = {}

def register_factor(name: str):
    """
    用作类装饰器：
    @register_factor("illiq_guiji")
    class IlliqGuijiFactor(BaseFactor):
        ...
    """
    def decorator(cls):
        FACTOR_REGISTRY[name] = cls
        return cls
    return decorator


def get_factor(name: str, **kwargs):
    """
    通过名字创建因子实例：
    factor = get_factor("illiq_guiji", window=20)
    """
    cls = FACTOR_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Factor {name} not found in registry.")
    return cls(**kwargs)


# =========================
# 因子基类
# =========================
class BaseFactor(abc.ABC):
    """
    通用因子基类：
    - 统一接口：run() / calculate()
    - 封装清洗、去极值、标准化、中性化等流程
    - 方便回测模块直接调用
    """

    def __init__(
        self,
        name: str,
        lookback: int | None = None,      # 回看窗口（天）
        lag: int = 1,                     # 滞后期，通常=1天
        winsor_limit: float = 0.01,       # 去极值比例 (1% / 99%)
        do_winsor: bool = False,
        do_zscore: bool = False,           # 是否做横截面标准化
        neutralize_cols: list[str] | None = None,  # 需要中性化的列，如 ["ln_mkt_cap"]
    ):
        self.name = name
        self.lookback = lookback
        self.lag = lag
        self.winsor_limit = winsor_limit
        self.do_winsor = do_winsor
        self.do_zscore = do_zscore
        self.neutralize_cols = neutralize_cols or []

    # -------- 外部主要调用入口 --------
    def run(self, panel: pd.DataFrame) -> pd.DataFrame:
        """
        panel: MultiIndex DataFrame
               index = [trade_date, asset] 或 columns 包含这两列
               至少包含本因子需要用到的原始字段
        返回:
            DataFrame: 与 panel 对齐，包含一列 self.name
        """
        # 统一一下索引格式：index = [trade_date, asset]
        panel = self._ensure_multiindex(panel)

        # 1. 计算原始因子值（子类实现）
        raw_factor = self.calculate(panel)

        # 2. 将 calculate() 的返回值转换为标准格式
        # calculate() 可能返回 Series 或 DataFrame，统一转换为 DataFrame
        if isinstance(raw_factor, pd.Series):
            factor_df = pd.DataFrame({self.name: raw_factor})
        elif isinstance(raw_factor, pd.DataFrame):
            # 如果返回的是 DataFrame，提取因子列
            if self.name in raw_factor.columns:
                factor_df = pd.DataFrame({self.name: raw_factor[self.name]})
            else:
                # 如果没有因子列，取第一列
                factor_df = pd.DataFrame({self.name: raw_factor.iloc[:, 0]})
        else:
            raise ValueError(f"calculate() must return pd.Series or pd.DataFrame, got {type(raw_factor)}")
        
        factor_df = factor_df.sort_index()

        # 3. 按日期横截面地做清洗和处理
        factor_df = self._post_process(panel, factor_df)

        # 4. 滞后处理（避免未来函数）
        if self.lag > 0:
            factor_df[self.name] = (
                factor_df.groupby(level=1)[self.name].shift(self.lag)
            )

        return factor_df

    @abc.abstractmethod
    def calculate(self, panel: pd.DataFrame) -> pd.DataFrame:
        """
        核心计算逻辑（子类实现）
        参数:
            panel: MultiIndex DataFrame, index=[trade_date, asset]
        返回:
            pd.Series，index 与 panel 对齐
        """
        raise NotImplementedError

    # -------- 公共工具函数（子类也可以调用） --------
    def _ensure_multiindex(self, df: pd.DataFrame) -> pd.DataFrame:
        """保证 index = [date, code] 的 MultiIndex 形式"""
        if isinstance(df.index, pd.MultiIndex):
            return df
        # 假设原本有 'date', 'code' 两列
        if {"date", "code"}.issubset(df.columns):
            df = df.set_index(["date", "code"])
        else:
            raise ValueError("panel 必须是 MultiIndex 或含有 'trade_date','asset' 列")
        return df

    def _post_process(self, panel: pd.DataFrame, factor_df: pd.DataFrame) -> pd.DataFrame:
        """封装：去极值 → 标准化 → 中性化"""
        name = self.name

        # 1. 去极值（横截面 winsor）
        if self.do_winsor:
            factor_df[name] = factor_df.groupby(level=0)[name].transform(
                lambda x: self._winsorize(x, self.winsor_limit)
            )

        # 2. 标准化（横截面 zscore）
        if self.do_zscore:
            factor_df[name] = factor_df.groupby(level=0)[name].transform(self._zscore)

        # 3. 中性化（对市值、行业等）
        if self.neutralize_cols:
            factor_df[name] = self._neutralize(panel, factor_df[name])

        return factor_df

    @staticmethod
    def _winsorize(x: pd.Series, limit: float) -> pd.Series:
        """按百分位数去极值"""
        lower = x.quantile(limit)
        upper = x.quantile(1 - limit)
        return x.clip(lower, upper)

    @staticmethod
    def _zscore(x: pd.Series) -> pd.Series:
        """横截面标准化"""
        mu = x.mean()
        sigma = x.std()
        if sigma == 0 or np.isnan(sigma):
            return x * np.nan
        return (x - mu) / sigma

    def _neutralize(self, panel: pd.DataFrame, factor: pd.Series) -> pd.Series:
        """
        简单线性回归中性化：
        因子 ~ neutralize_cols
        残差作为新的因子值
        """
        # panel 和 factor 已经是 MultiIndex 对齐的
        df = panel.copy()
        df[self.name] = factor

        results = []

        for date, sub in df.groupby(level=0):
            y = sub[self.name]
            X_cols = [c for c in self.neutralize_cols if c in sub.columns]
            if not X_cols:
                results.append(y)
                continue

            X = sub[X_cols].astype(float)
            X = X.fillna(X.mean())  # 简单填充
            X = np.column_stack([np.ones(len(X)), X.values])  # 加截距

            mask = ~y.isna() & ~np.isnan(X).any(axis=1)
            if mask.sum() < len(X_cols) + 2:
                results.append(y)
                continue

            beta, *_ = np.linalg.lstsq(X[mask], y[mask].values, rcond=None)
            y_hat = X @ beta
            resid = y - y_hat
            resid[~mask] = np.nan
            results.append(resid)

        resid_all = pd.concat(results).sort_index()
        return resid_all
