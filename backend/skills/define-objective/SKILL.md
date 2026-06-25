---
name: define-objective
description: 梳理工艺参数优化的目标和约束条件，明确优化方向。当用户提出工艺优化需求时，第一步使用本技能明确目标。
---

# 梳理优化目标

## When to Use
当用户提出工艺参数优化需求时，第一步使用本 Skill 来明确目标。

## Steps
1. 明确优化目标（提升良率/降低能耗/提高效率等）
2. 定义量化指标（目标值 + 可接受范围）
3. 明确约束条件（成本限制/安全要求/生产节拍等）
4. 收集基线数据（当前工艺参数的取值和对应输出）
5. 确定优化范围（哪些参数可调，哪些固定）
6. 输出结构化的优化目标文档

## Output Format
输出应包含: objective, success_criteria, constraints, baseline_data
