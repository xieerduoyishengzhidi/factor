# 量化因子研究与回测框架

一个用于股票横截面因子研究的 Python 工程框架，支持因子构建、预处理、评估和回测分析。

## 📋 目录

- [项目简介](#项目简介)
- [文件结构](#文件结构)
- [快速开始](#快速开始)
- [使用流程](#使用流程)
- [因子开发指南](#因子开发指南)
- [未来扩展方向](#未来扩展方向)

## 🎯 项目简介

本框架专注于量化因子的研究与评估，提供完整的因子研究流程：

- **因子构建**：基于 `BaseFactor` 基类，快速开发新因子
- **因子预处理**：去极值、标准化、中性化等处理
- **因子评估**：IC 分析、分层回测、换手率分析等
- **策略回测**：基于因子的简单轮动策略
- **结果可视化**：自动生成图表和报告

### 核心特性

- ✅ 统一的因子接口设计，易于扩展
- ✅ 完整的因子评估体系（IC、分层回测等）
- ✅ 自动化的数据预处理流程
- ✅ 结果自动保存和可视化
- ✅ 支持多种市场收益计算方式（等权、市值加权、成交额加权）

## 📁 文件结构

```
factor/
│
├── data/                          # 数据目录
│   ├── raw/                       # 原始数据（外部导入，只读）
│   │   ├── CLOSE.pkl             # 收盘价
│   │   ├── HIGH.pkl              # 最高价
│   │   ├── LOW.pkl               # 最低价
│   │   ├── OPEN.pkl              # 开盘价
│   │   ├── VOLUME.pkl            # 成交量
│   │   ├── TURNOVER.pkl          # 成交额
│   │   ├── market_cap.pkl        # 流通市值
│   │   └── DAILY_TURNOVER_RATE.pkl
│   ├── interim/                   # 中间处理数据
│   │   └── panel_aligned.pkl     # 对齐后的面板数据
│   ├── processed/                 # 清洗后的数据
│   │   └── panel_cleaned.pkl     # 最终清洗的面板数据
│   ├── factors/                   # 因子计算结果
│   │   ├── illiq_guiji.pkl       # 非流动性因子
│   │   └── panic_factor.pkl      # 惊恐因子
│   └── results/                   # 评估结果和图表
│       ├── {因子名}_ic_analysis.png
│       └── {因子名}_layer_backtest.png
│
├── preprocess/                    # 数据预处理模块
│   ├── load_data.py              # 加载原始数据
│   ├── align_data.py             # 数据对齐（日期×代码）
│   └── clean_data.py             # 数据清洗（停牌、缺失值处理）
│
├── factors/                       # 因子实现模块
│   ├── base_factor.py            # 因子基类（统一接口）
│   ├── illiq_guiji.py            # 非流动性因子实现
│   └── panic_factor.py           # 惊恐因子实现
│
├── factor_processing/             # 因子处理模块
│   ├── winsorize.py              # 去极值
│   ├── standardize.py            # 标准化
│   ├── neutralize.py             # 中性化
│   └── factor_pipeline.py        # 因子处理流水线
│
├── factor_evaluation/             # 因子评估模块
│   ├── util.py                   # 工具函数
│   ├── ic_analysis.py            # IC 分析（IC、ICIR、胜率）
│   ├── layer_backtest.py         # 分层回测
│   ├── factor_return_regression.py  # 因子收益回归
│   ├── turnover_analysis.py      # 换手率分析
│   └── summary_report.py         # 汇总报告
│
├── strategy/                       # 策略模块
│   ├── single_factor_strategy.py # 单因子策略
│   └── position_sizing.py        # 仓位管理
│
├── backtest/                       # 回测引擎
│   ├── engine.py                 # 回测引擎
│   └── performance.py            # 绩效统计
│
├── utils/                          # 工具函数
│   ├── io.py                     # 文件读写
│   ├── log.py                    # 日志工具
│   ├── calendar.py               # 交易日工具
│   └── plot.py                   # 绘图工具
│
├── load_data.py                    # 数据加载脚本（用于因子计算）
├── run.py                          # 因子评估主程序
└── README.md                       # 本文件
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pandas
- numpy
- matplotlib

### 安装依赖

```bash
pip install pandas numpy matplotlib
```

### 数据准备

1. 将原始数据放入 `data/raw/` 目录
2. 运行数据预处理脚本：

```bash
# 数据对齐
python preprocess/align_data.py

# 数据清洗
python preprocess/clean_data.py
```

## 📖 使用流程

### 1. 数据预处理

数据预处理分为三个步骤：

#### 步骤 1：加载原始数据
```python
from preprocess.load_data import load_data

close, high, low, open_price, volume, market_capitalization, turnover, daily_turnover_rate = load_data()
```

#### 步骤 2：数据对齐
```python
from preprocess.align_data import load_raw, align_data

dfs = load_raw()
aligned_dict, panel = align_data(dfs)
```

#### 步骤 3：数据清洗
```python
from preprocess.clean_data import load_panel, add_status_fields

panel = load_panel()
panel_cleaned = add_status_fields(panel)
```

### 2. 计算因子

#### 方法一：使用现有因子

以惊恐因子为例：

```python
import pandas as pd
import os
from factors.base_factor import get_factor
import factors.panic_factor  # 导入因子模块以注册因子
from load_data import load_panel_data

# 加载数据
panel = load_panel_data()

# 创建因子实例
factor = get_factor("panic_factor", lookback=21, weight_method='equal')

# 计算因子
result = factor.run(panel)

# 保存结果
result.reset_index().to_pickle('data/factors/panic_factor.pkl')
```

#### 方法二：开发新因子

参考 [因子开发指南](#因子开发指南) 部分。

### 3. 因子评估

运行评估脚本：

```bash
python run.py --factor_name panic_factor
```

评估流程包括：

1. **IC 分析**
   - 计算日度 IC 序列
   - 计算 IC 均值、标准差、ICIR
   - 计算胜率（IC > 0 的占比）
   - 生成 IC 分析图

2. **分层回测**
   - 按因子值分为 5 组
   - 计算各组等权收益
   - 计算多空收益（Top - Bottom）
   - 生成分层回测图

结果自动保存到 `data/results/` 目录：
- `{因子名}_ic_analysis.png` - IC 分析图
- `{因子名}_layer_backtest.png` - 分层回测图

## 🔧 因子开发指南

### 创建新因子

1. **在 `factors/` 目录下创建新文件**，例如 `my_factor.py`：

```python
# factors/my_factor.py
from factors.base_factor import BaseFactor, register_factor
import pandas as pd
import numpy as np

@register_factor("my_factor")
class MyFactor(BaseFactor):
    
    def __init__(self, lookback=20, **kwargs):
        super().__init__(name="my_factor", lookback=lookback, **kwargs)
    
    def calculate(self, panel: pd.DataFrame) -> pd.Series:
        """
        计算因子值
        
        参数:
            panel: MultiIndex DataFrame, index=['date', 'code']
                   包含 close, high, low 等列
        
        返回:
            pd.Series: 因子值，index 与 panel 对齐
        """
        # 1. 检查索引格式
        if not isinstance(panel.index, pd.MultiIndex) or panel.index.names != ['date', 'code']:
            raise ValueError("panel 必须是 MultiIndex, 且 index 顺序为 ('date', 'code')")
        
        # 2. 实现因子计算逻辑
        # 例如：计算滚动收益率的标准差
        ret = panel['close'].groupby('code').pct_change()
        result = ret.groupby('code').rolling(
            window=self.lookback,
            min_periods=self.lookback // 2
        ).std()
        
        # 3. 索引对齐（重要！）
        if result.index.nlevels > 2:
            result = result.droplevel(level=0)
        if result.index.names != panel.index.names:
            result.index.set_names(panel.index.names, inplace=True)
        if result.index.names[0] != 'date':
            result = result.swaplevel('date', 'code')
        
        result = result.sort_index().reindex(panel.index)
        
        # 4. 处理停牌等情况
        mask_no_close = panel['close'].isna()
        result[mask_no_close] = np.nan
        
        return result
```

2. **使用因子**：

```python
from factors.base_factor import get_factor
import factors.my_factor  # 导入以注册因子

factor = get_factor("my_factor", lookback=20)
result = factor.run(panel)
```

### BaseFactor 基类说明

所有因子继承自 `BaseFactor`，提供以下功能：

- **统一接口**：`calculate()` 方法实现因子计算逻辑
- **自动处理**：去极值、标准化、中性化（可选）
- **滞后处理**：避免未来函数
- **索引对齐**：自动处理 MultiIndex 对齐问题

#### 初始化参数

```python
BaseFactor(
    name: str,                      # 因子名称
    lookback: int | None = None,    # 回看窗口（天）
    lag: int = 0,                   # 滞后期（通常=0天）
    winsor_limit: float = 0.01,     # 去极值比例 (1% / 99%)
    do_winsor: bool = False,        # 是否去极值
    do_zscore: bool = False,        # 是否标准化
    neutralize_cols: list[str] | None = None,  # 需要中性化的列
)
```

### 已实现的因子

#### 1. 非流动性因子 (illiq_guiji)

- **文件**：`factors/illiq_guiji.py`
- **公式**：`sum(log(1 + |ret|)) / sum(amount)` over lookback window
- **参数**：`lookback=20`（默认）

#### 2. 惊恐因子 (panic_factor)

- **文件**：`factors/panic_factor.py`
- **公式**：
  1. 市场收益：`r_m,t = (1/N_t) * Σ r_i,t`（等权）或加权
  2. 惊恐度：`panic_i,t = |r_i,t - r_m,t| / (|r_i,t| + |r_m,t| + 0.1)`
  3. 惊恐收益：`x_i,t = panic_i,t * r_i,t`
  4. 因子值：`factor_i,t = StdDev(x_i,t-20, ..., x_i,t)`（21日标准差）
- **参数**：
  - `lookback=21`：滚动窗口大小
  - `weight_method='equal'`：市场收益计算方式（'equal'/'market_cap'/'turnover'）

## 🔮 未来扩展方向

### 短期计划（V1.1）

1. **因子处理增强**
   - [ ] 支持更多中性化方法（行业、市值等）
   - [ ] 支持因子组合（多因子合成）
   - [ ] 因子有效性检验（稳定性、单调性等）

2. **评估指标扩展**
   - [ ] 月度/年度 IC 分析
   - [ ] 因子收益回归分析
   - [ ] 换手率分析完善
   - [ ] 因子衰减分析

3. **可视化增强**
   - [ ] 因子分布图
   - [ ] 因子相关性热力图
   - [ ] 多因子对比分析图
   - [ ] 自动生成 PDF 报告

### 中期计划（V2.0）

1. **策略回测完善**
   - [ ] 支持多因子组合策略
   - [ ] 支持风险模型（Barra 等）
   - [ ] 支持交易成本建模
   - [ ] 支持持仓限制（行业、市值等）

2. **性能优化**
   - [ ] 并行计算支持
   - [ ] 大数据集优化
   - [ ] 缓存机制

3. **数据源扩展**
   - [ ] 支持更多数据格式（CSV、Parquet、数据库）
   - [ ] 支持实时数据接入
   - [ ] 数据质量检查工具

### 长期计划（V3.0+）

1. **机器学习集成**
   - [ ] 因子挖掘（特征工程）
   - [ ] 因子选择（特征选择）
   - [ ] 非线性因子合成

2. **实盘对接**
   - [ ] 券商 API 接口
   - [ ] 实时因子计算
   - [ ] 自动交易执行

3. **框架完善**
   - [ ] Web 界面（因子管理、回测可视化）
   - [ ] 配置管理系统
   - [ ] 版本控制和实验管理

## 📝 注意事项

1. **数据格式要求**
   - Panel 数据必须是 MultiIndex，格式为 `index=['date', 'code']`
   - 日期必须按升序排列
   - 确保数据已对齐（日期和代码的交集）

2. **因子计算**
   - 因子计算必须避免未来函数
   - 注意处理停牌、缺失值等情况
   - 确保返回值的索引与输入 panel 完全对齐

3. **性能考虑**
   - 大数据集建议使用分块处理
   - 因子计算结果建议缓存
   - 避免在循环中进行大量数据操作



