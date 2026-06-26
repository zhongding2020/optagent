---
name: generate-report
description: 基于分析结果生成工艺参数优化验证报告，包含推荐参数和下一步建议。
---

# 生成验证报告

## 核心规则
- **严禁**生成或执行 Python/代码。使用结构化对话生成报告内容。
- 完成本步骤后务必调用 `step_complete` 工具。

## Steps

### 1. 优化过程回顾
- 初始目标回顾
- 关键参数汇总
- DOE方案概述

### 2. 分析结果总结
- 关键因子及影响排序
- 最优参数组合推荐
- 预期改善幅度

### 3. 验证建议
- 验证试验方案
- 确认运行的条件
- 风险提示

### 4. 下一步建议
- 持续监控方案
- 潜在的进一步优化方向
- 知识沉淀建议

### 5. 输出报告摘要
- 调用 `step_complete` 工具，输出格式：
```
{
  "optimization_summary": "概述",
  "recommended_params": {"参数名": "推荐值"},
  "expected_improvement": "预期改善",
  "confidence_level": "置信水平",
  "next_steps": ["下一步1", "下一步2"]
}
```
