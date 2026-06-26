---
name: analyze-results
description: 对试验数据进行统计分析，提取关键因子、评估影响大小、相关性分析和交互效应。
---

# 数据分析与因子提取

## 核心规则（重要）
- **严禁**生成或执行任何 Python/R/代码。使用内置分析工具进行计算。
- 不要在回答中编写代码块（```python ... ```）。
- 完成本步骤后务必调用 `step_complete` 工具。
- 在 `step_complete` 中输出包含数值因子的摘要（格式如"温度: 42%, 压力: 35%"），以便后续图表展示。

## 可用工具

当用户提供了试验数据时，使用以下分析工具进行计算：

### `correlation_analysis(data_json, columns)`
- 计算因子间的 Pearson 相关系数矩阵
- 返回相关系数、p值（scipy可用时）、因子对强度判断
- **适用场景**：用户提供多因子试验数据后，分析因子间相关性

### `factor_importance(data_json, target_column, feature_columns)`
- 标准化回归系数法评估各因子对目标的影响大小
- 返回排序后的因子重要性列表（含百分比）
- **适用场景**：确定哪些因子对良率/质量影响最大

### `pareto_analysis(data_json, category_column, value_column)`
- 帕累托分析：按影响大小排序，计算累计百分比
- 识别"关键的少数"因子
- **适用场景**：展示因子贡献的"二八原则"

### `design_experiment(factors, levels, design_type)`
- 生成试验设计矩阵（全因子/中心复合设计）
- **适用场景**：帮助用户规划试验方案
- 设计类型：`full_factorial` | `central_composite`

### `response_surface(data_json, factors, response_column)`
- 拟合二阶响应面模型 y = b0 + Σbi*xi + Σbii*xi² + Σbij*xi*xj
- 返回最优参数组合和预测最优值
- **适用场景**：找到最佳工艺参数窗口

### `anova_one_way(data_json, factor_column, response_column)`
- 单因素方差分析，检验不同因子水平对结果影响的显著性
- 返回 F 统计量、p值、组统计量
- **适用场景**：判断某个工艺参数的调整是否显著影响质量

## 数据格式

所有分析工具接受统一的数据格式：
```json
{
  "columns": ["温度", "压力", "时间", "良率"],
  "rows": [[150, 3, 30, 82], [160, 4, 45, 85], ...]
}
```

用户可能在对话中用自然语言描述数据，你需要将其整理为上述 JSON 格式再传入工具。

## Steps

### 1. 收集数据
- 如果用户还没有系统数据，引导用户提供试验结果
- 可以是表格、列表或自然语言描述
- 将数据整理为标准 JSON 格式

### 2. 因子效应分析
- 调用 `factor_importance` 工具分析各因子影响大小
- 讨论哪些因子对目标影响最大
- 按影响大小对因子排序

### 3. Pareto 分析
- 调用 `pareto_analysis` 工具
- 识别"关键的少数"因子
- 建议优先关注前2-3个关键因子

### 4. 相关性分析
- 调用 `correlation_analysis` 工具
- 讨论因子之间的相关性方向
- 识别可能的多重共线性问题

### 5. 响应面分析（可选）
- 如果数据充分，调用 `response_surface` 工具
- 找到最优工艺参数组合
- 预测最优结果

### 6. 方差分析
- 调用 `anova_one_way` 工具验证因子显著性
- 判断统计显著性

### 7. 输出分析结果
- 调用 `step_complete` 工具，输出包含数值的摘要：
```
分析完成。关键因子排序：
温度: 42%
压力: 35%
时间: 28%
pH: 15%
速度: 8%
最优参数组合: 温度=165°C, 压力=4.5bar, 时间=40s
预期良率: 93.5%
```
数值格式对图表展示至关重要。
