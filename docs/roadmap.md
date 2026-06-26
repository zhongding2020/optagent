# OptAgent 功能实现路线图

> 最后更新：2026-06-26 12:00 — **全部 15 项功能已完成**
> 验证测试：`python3 tests/test_verify.py`（快速模式 11/11 通过）
> 完整验证：`python3 tests/test_verify.py --all`（15 项覆盖）

---

## 整体完成度

| 层级 | 状态 | 项数 | 说明 |
|------|------|------|------|
| P0 | ✅ 全部完成 | 1-4 | 核心流程：LangGraph + deepagents + 事件流 + KB |
| P1 | ✅ 全部完成 | 5-7 | 数据链路：Data 端点 + Analysis 图表 + WorkflowGraph |
| P2 | ✅ 全部完成 | 8-11 | 生产化：URL 配置 + 终止 + Checkpoint + 加载态 |
| P3 | ✅ 全部完成 | 12-15 | 扩展：backends + 状态端点 + Embedding + 上下文优化 |

---

## P0 — 核心流程打通

| # | 功能 | 描述 | 文件 |
|---|------|------|------|
| 1 | LangGraph 执行路径 | 首条消息触发 `graph:start` + `node:enter`，逐节点推进（`step_complete` → 下一节点） | `main.py`, `session_manager.py` |
| 2 | deepagents 集成 | `agent.astream_events()` + `create_deep_agent(tools=...)`，SkillsMiddleware 激活 | `main.py`, `agent/factory.py` |
| 3 | 事件流接入 | `agent.astream_events()` 替代手动事件构建，token/tool_call/message 实时推送 | `main.py` |
| 4 | KB Tool 绑定 | `query_knowledge_base` + `step_complete` 传入 `create_deep_agent()` | `main.py`, `agent/tools.py` |

## P1 — Analysis 数据链路

| # | 功能 | 描述 | 文件 |
|---|------|------|------|
| 5 | `GET /api/sessions/:id/data` | 从 `node_results` 提取因子排序、Pareto、相关性、设计矩阵、散点趋势 | `server/routes/data.py`, `models/session.py` |
| 6 | Analysis 图表接真实数据 | 5 个 ECharts 组件从 API 获取数据，支持数据空态与加载态 overlay | `pages/Analysis.tsx`, `charts/*` |
| 7 | WorkflowGraph 状态更新 | 连线颜色按节点状态变化（completed=green, running=blue），运行节点脉冲动画 | `components/WorkflowGraph.tsx` |

## P2 — 生产化

| # | 功能 | 描述 | 文件 |
|---|------|------|------|
| 8 | URL 配置化 | `VITE_WS_URL` / `VITE_API_URL` 环境变量，fallback 到 `localhost:8020` | `hooks/useWebSocket.ts`, `hooks/useApi.ts` |
| 9 | 终止机制 | `cancel_event` 传递到 `_chat_with_agent()`，流式循环中检查中断信号 | `main.py` |
| 10 | Checkpoint 持久化 | Session 消息持久化至 SQLite，断线重连自动恢复对话历史 | `persistence/store.py`, `main.py` |
| 11 | Loading/Error 状态 | Dashboard 骨架屏加载态 + 错误横幅 + 重试按钮；WS 断线自动重连 | `pages/Dashboard.tsx`, `hooks/useWebSocket.ts` |

## P3 — 扩展能力

| # | 功能 | 描述 | 文件 |
|---|------|------|------|
| 12 | `backends/` 抽象 | 注册表模式：`register()`/`get_backend()`/`list_backends()` + StorageBackend 基类 | `backends/__init__.py` |
| 13 | 状态 REST 端点 | `GET /api/sessions/:id/state` — 含 message_count、node_statuses、node_results | `server/routes/sessions.py` |
| 14 | Embedding 升级 | ONNX 自动检测 + 优雅回退到 ngram，子线性 TF 缩放提升质量，配置驱动模型选择 | `kb/embedding.py`, `config.py` |
| 15 | 多轮对话上下文优化 | 消息裁剪保留最近 30 轮（MAX=30），超限自动折叠 + 摘要占位符 | `main.py` |

---

## 架构

```
用户发消息 → WebSocket handler
  ├─ 首次消息 → _start_workflow()
  │  ├─ graph:start → 前端 WorkflowGraph
  │  └─ node:enter（define_objective）
  ├─ _chat_with_agent()
  │  ├─ agent.astream_events() ← deepagents + SkillsMiddleware
  │  ├─ 渐进式技能加载 / tool calling (query_kb, step_complete)
  │  ├─ 检测 step_complete → _advance_workflow()
  │  │   ├─ node:exit（当前节点 + 耗时）
  │  │   └─ node:enter（下一节点）/ graph:end（完成）
  │  └─ _persist_session_messages() → 消息裁剪 + SQLite 持久化
  └─ 前端展示 chat 消息 + 工作流状态 + 控制按钮
```

---

## 已有功能清单

### 后端

| # | 功能 | 状态 | 说明 |
|---|------|------|------|
| B1 | FastAPI 服务 | ✅ | WebSocket + REST，端口 8020 |
| B2 | 配置系统 | ✅ | `config.yaml` 多模块配置 |
| B3 | Agent Factory | ✅ | 支持 DeepSeek/OpenAI/Anthropic/Ollama |
| B4 | Skills 热插拔 | ✅ | 注册/卸载/重载，REST API |
| B5 | 知识库 Chroma | ✅ | 上传/搜索/统计 |
| B6 | 本地 ngram 嵌入 | ✅ | 零依赖零下载，512 维，支持 ONNX 升级 |
| B7 | KB 统计 | ✅ | 查询次数/命中率/热门来源/查询历史 |
| B8 | Session 管理 | ✅ | SQLite 持久化，消息 Checkpoint |
| B9 | Workflow 加载 | ✅ | YAML 定义 → StateGraph 构建 |
| B10 | Node Runner | ✅ | 节点执行循环（集成到 chat 流程） |
| B11 | Chat 事件流 | ✅ | `agent.astream_events()` + step_complete 检测 |
| B12 | 终止机制 | ✅ | cancel_event 检查 + session_manager.terminate() |
| B13 | 后端表格修复 | ✅ | `_fix_markdown_tables()` |
| B14 | CORS / 心跳 | ✅ | 跨域配置 + WS 30s heartbeat |
| B15 | Backend 注册表 | ✅ | 注册模式可扩展存储后端 |
| B16 | 状态端点 | ✅ | `GET /api/sessions/:id/state` |
| B17 | 消息上下文优化 | ✅ | 保留 30 轮，自动裁剪持久化 |

### 前端

| # | 功能 | 状态 | 说明 |
|---|------|------|------|
| F1 | React SPA | ✅ | Vite + TypeScript + Router |
| F2 | Dashboard | ✅ | 骨架屏加载态 + 错误重试 |
| F3 | WorkflowDetail | ✅ | 聊天 + WorkflowGraph + 侧边栏 |
| F4 | Chat 全屏页 | ✅ | 全屏 agent 对话 |
| F5 | KnowledgeBase 管理 | ✅ | 四标签页 |
| F6 | 侧边栏导航 | ✅ | Session 列表 + 快捷入口 |
| F7 | 暗亮主题切换 | ✅ | CSS 变量 |
| F8 | AgentChat | ✅ | markdown 渲染 + remark-gfm |
| F9 | ChatInput | ✅ | 居中输入框 |
| F10 | KB 组件 | ✅ | KbSearchResult/DocumentList/UploadProgress |
| F11 | WorkflowGraph | ✅ | 连线颜色 + 脉冲动画 + 耗时展示 |
| F12 | SkillStatus | ✅ | 匹配技能展示 |
| F13 | TerminateButton / NextStepButton | ✅ | 控制按钮 |
| F14 | WS 自动重连 | ✅ | 断线 2s 重试 + 错误状态 |
| F15 | URL 配置化 | ✅ | VITE_API_URL / VITE_WS_URL 环境变量 |
| F16 | Analysis 页 | ✅ | 5 个 ECharts 图表接真实数据 + 空态展示 |

### 技能

| # | 技能 | 说明 |
|---|------|------|
| S1 | define-objective | 梳理优化目标 |
| S2 | identify-params | 识别关键工艺参数 |
| S3 | design-doe | 试验设计（DOE） |
| S4 | collect-data | 收集试验结果 |
| S5 | analyze-results | 数据分析与因子提取 |
| S6 | generate-report | 生成验证报告 |
| S7 | knowledge-retrieval | 知识库检索辅助 |

### 工作流

| # | 工作流 | 说明 |
|---|--------|------|
| W1 | process-optimization | 6 步工艺优化流程（YAML 定义） |

---

## 验证测试

```bash
# 快速测试（11 项，无 WebSocket）
python3 tests/test_verify.py

# 全部测试（15 项，含 WebSocket）
python3 tests/test_verify.py --all

# 按层级筛选
python3 tests/test_verify.py --p0/--p1/--p2/--p3

# 调整 WS 超时（默认 15s）
python3 tests/test_verify.py --all --timeout 30
```

---

## 后续方向

| 方向 | 说明 |
|------|------|
| 更多 workf low | 扩展 YAML 定义（热处理、压铸、CNC 等） |
| 更多 skills | 领域专家 skills 持续积累 |
| 部署生产化 | 域名 + HTTPS + 反向代理 |
| 用户认证 | 登录 / 权限 / 多租户 |
| 多语言 | 国际化技能与 UI |
