# OptAgent 功能实现路线图

> 最后更新：2026-06-25 21:30
> 最后更新：2026-06-25 22:30
> 最后更新：2026-06-26 01:30
> 最后更新：2026-06-26 11:00
> 用途：追踪设计与实现的差距，持续刷新功能完成状态

---

## 图例

- [x] 已完成
- [~] 部分完成 / 有缺陷
- [ ] 未开始

---

## P0 — 核心流程打通（使 Workflow 真正运行）

| # | 功能 | 描述 | 状态 | 文件 |
|---|------|------|------|------|
| 1 | LangGraph 执行路径 | 创建 Session 后触发 `_run_workflow()`，走完整 NodeRunner 循环 | [ ] | `main.py`, `session_manager.py` |
 | 1 | LangGraph 执行路径 | 首条消息触发 `graph:start` + `node:enter`，逐节点推进（step_complete → 下一节点 | [x] | `main.py`, `session_manager.py` |
| 2 | 正确使用 deepagents | `agent.astream_events()` + `create_deep_agent(tools=...)`，激活 SkillsMiddleware | [x] | `main.py`, `agent/factory.py` |
| 3 | 事件流接入 | 使用 `agent.astream_events()` 替代手动事件构建 | [x] | `main.py` |
| 4 | KB Tool 绑定 | `query_knowledge_base` 和 `step_complete` 传入 `create_deep_agent()` | [x] | `main.py`, `agent/tools.py` |

## P1 — Analysis 数据链路

| # | 功能 | 描述 | 状态 | 文件 |
|---|------|------|------|------|
| 5 | `GET /api/sessions/:id/data` | 从 `node_results` 提取因子排序、相关性等 | [ ] | `server/routes/data.py` |
 | 5 | `GET /api/sessions/:id/data` | 从 `node_results` 提取分析数据，含因子排序、Pareto、相关性、设计矩阵 | [x] | `server/routes/data.py`, `models/session.py` |
| 6 | Analysis 图表接真实数据 | 5 个 ECharts 组件从 API 获取数据 | [ ] | `pages/Analysis.tsx`, `charts/*` |
 | 6 | Analysis 图表接真实数据 | 5 个 ECharts 组件从 API 获取数据，支持数据空态与加载态 | [x] | `pages/Analysis.tsx`, `charts/*` |
| 7 | WorkflowGraph 状态更新 | 根据 WS 事件实时更新节点状态 | [ ] | `components/WorkflowGraph.tsx` |
 | 7 | WorkflowGraph 状态更新 | 连线颜色根据节点状态变化（completed=green, running=blue），运行节点脉冲动画 | [x] | `components/WorkflowGraph.tsx` |

## P2 — 生产化

| # | 功能 | 描述 | 状态 | 文件 |
|---|------|------|------|------|
| 8 | URL 配置化 | WebSocket/API base 从 config 或环境变量读取 | [ ] | `hooks/useWebSocket.ts`, `hooks/useApi.ts` |
 | 8 | URL 配置化 | WebSocket/API base 从环境变量读取 (VITE_WS_URL, VITE_API_URL) | [x] | `hooks/useWebSocket.ts`, `hooks/useApi.ts` |
| 9 | 终止机制 | `SessionManager.start_execution()` 接入 `_run_workflow` | [ ] | `session_manager.py`, `main.py` |
 | 9 | 终止机制 | cancel_event 传递到 _chat_with_agent，流式循环中检查中断 | [x] | `main.py` |
| 10 | Checkpoint 持久化 | Session 支持断点续传 | [ ] | `workflow/builder.py`, `persistence/store.py` |
| 11 | Loading/Error 状态 | 所有页面添加加载态和错误处理 | [ ] | `pages/*.tsx` |
 | 11 | Loading/Error 状态 | Dashboard 添加骨架屏加载态 + 错误提示 + 重试按钮 | [x] | `pages/Dashboard.tsx` |

## P3 — 扩展能力

| # | 功能 | 描述 | 状态 | 文件 |
|---|------|------|------|------|
| 12 | `backends/` 实现 | 支持不同存储后端 | [ ] | `backends/` |
| 13 | 缺失 REST 端点 | `/resume`, `/state`, `/data` 等 | [ ] | `server/routes/sessions.py` |
| 14 | Embedding 模型升级 | 从 ngram 换回 ONNX/BGE（网络改善后） | [ ] | `kb/embedding.py` |
| 15 | 多轮对话上下文优化 | Session 消息历史管理策略 | [ ] | `main.py` |

---

## 已有功能清单

### 后端

| # | 功能 | 状态 | 说明 |
|---|------|------|------|
| B1 | FastAPI 服务 | [x] | WebSocket + REST，端口 8020 |
| B2 | 配置系统 | [x] | `config.yaml` 多模块配置 |
| B3 | Agent Factory | [x] | 支持 DeepSeek/OpenAI/Anthropic/Ollama |
| B4 | Skills 热插拔 | [x] | 注册/卸载/重载，REST API |
| B5 | 知识库 Chroma | [x] | 上传/搜索/统计 |
| B6 | 本地 ngram 嵌入 | [x] | 零依赖零下载，512 维 |
| B7 | KB 统计 | [x] | 查询次数/命中率/热门来源/查询历史 |
| B8 | Session 管理 | [x] | SQLite 持久化 |
| B9 | Workflow 加载 | [x] | YAML 定义 → StateGraph 构建 |
| B10 | Node Runner | [x] | Residence loop 模式 |
| B11 | Chat 技能注入 | [x] | 手写 system prompt 注入 |
| B12 | Chat KB 注入 | [x] | 手动搜索 KB 后注入 context |
| B13 | 后端表格修复 | [x] | `_fix_markdown_tables()` |
| B14 | CORS / 心跳 | [x] | 跨域配置 + WS 30s heartbeat |
| B15 | 事件类型定义 | [~] | 定义了但 `EventTransformer` 未接入 |

### 前端

| # | 功能 | 状态 | 说明 |
|---|------|------|------|
| F1 | React SPA | [x] | Vite + TypeScript + Router |
| F2 | Dashboard | [x] | 工作流列表 + 最近会话 |
| F3 | WorkflowDetail | [x] | 聊天 + WorkflowGraph + 侧边栏 |
| F4 | Chat 全屏页 | [x] | 全屏 agent 对话 |
| F5 | KnowledgeBase 管理 | [x] | 四标签页 |
| F6 | 侧边栏导航 | [x] | Session 列表 + 快捷入口 |
| F7 | 暗亮主题切换 | [x] | CSS 变量 |
| F8 | AgentChat | [x] | markdown 渲染 + remark-gfm |
| F9 | ChatInput | [x] | 居中输入框 |
| F10 | KB 组件 | [x] | KbSearchResult/DocumentList/UploadProgress |
| F11 | WorkflowGraph | [x] | 节点状态可视化 |
| F12 | SkillStatus | [x] | 匹配技能展示 |
| F13 | TerminateButton / NextStepButton | [x] | 控制按钮 |
| F14 | WS 自动重连 | [x] | 断线 1s 重试 |
| F15 | Analysis 页 | [~] | 5 个图表组件已搭建，数据未接入 |

### 技能

| # | 技能 | 状态 |
|---|------|------|
| S1 | define-objective | [x] |
| S2 | identify-params | [x] |
| S3 | design-doe | [x] |
| S4 | collect-data | [x] |
| S5 | analyze-results | [x] |
| S6 | generate-report | [x] |
| S7 | knowledge-retrieval | [x] |

### 工作流

| # | 工作流 | 状态 | 说明 |
|---|--------|------|------|
| W1 | process-optimization | [x] | 6 步工艺优化流程，YAML 定义 |

---

## 架构对比

### 当前
```
用户发消息 → WebSocket handler
  ├─ 首次消息 → _start_workflow()
  │  ├─ graph:start → 前端 WorkflowGraph
  │  └─ node:enter（define_objective）
  ├─ _chat_with_agent()
  │  ├─ agent.astream_events() ← deepagents + SkillsMiddleware
  │  ├─ 渐进式技能加载 on_tool_call
  │  └─ 检测 step_complete → _advance_workflow()
  │     ├─ node:exit（当前节点）
  │     └─ node:enter（下一节点）/ graph:end（完成）
  └─ 前端展示 chat 消息 + 工作流状态
```

### 目标
```
用户发消息 → WebSocket handler
  ├─ 工作流状态管理（_workflow_states）
  ├─ _chat_with_agent() + step_complete 检测
  ├─ _advance_workflow() 推进节点
  └─ 渐进式技能加载 + KB tool calling
```

---

## 更新方式

完成某个功能后，将对应 `[ ]` 改为 `[x]` 并更新顶部日期。
新增功能时在对应分类末尾追加新行。
子任务用 `| 1.1 | 描述 | [ ] | 文件 |` 格式。
