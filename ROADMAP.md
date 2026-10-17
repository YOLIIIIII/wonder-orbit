# WonderOrbit 路线图

更新日期：2026-10-17（Asia/Shanghai）。阶段与顺序以本文件说明；正式任务的当前状态、依赖和验收只在 [PRODUCT_BACKLOG](docs/PRODUCT_BACKLOG.md) 维护，来源见 [IDEA_LOG](docs/IDEA_LOG.md)，交付见 [CHANGELOG](CHANGELOG.md)，实证见 [VERIFICATION](docs/VERIFICATION.md)。里程碑名称不代表已发布版本或 Git tag。

## 当前阶段

**M1 本地 MVP 已交付并通过 Mock + SQLite 验收；M2 体验修整仍待实施。** 当前按用户范围优先修复 M3 的 INFRA-003 首次 CI 故障，并完成 INFRA-007 本地提交身份修正；不实施体验功能。远程历史改写推送仍待用户明确批准。没有整体完成百分比，尚未进入生产或多用户验收。

2026-10-17 本地回归为后端 47 passed / 1 skipped、前端 9 passed；本机 PostgreSQL 未配置。首次远程前端和 PG 迁移/schema 检查通过，普通 pytest 失败，独立 PG 集成步骤未执行；本地 CI 修复尚待远程验证，细节见 VERIFICATION。

## M1 / v0.1：本地 MVP（已交付，验证范围有限）

- Star CRUD、单张结构化待确认草稿、原始内容与来源追溯。
- 关键词/标签检索和真实共同标签/类别关联。
- LangGraph 分支、八个受控工具、确定性约束、显式审批。
- 用户反馈、候选偏好查看/确认/删除；确认后的明确偏好可编辑。
- Mock、独立模型适配层、运行审计、幂等键、安全生成重试。
- React 页面、紫色/暖黄/奶油白的原创响应式视觉与可替换占位形象。
- SQLAlchemy/Alembic 与 SQLite 迁移、规则/API/组件检查；开发阶段已运行隔离浏览器闭环。
- Compose、Nginx、GitHub Actions 和 PostgreSQL 测试配置已建立，执行验收归 M3。
- 中文 README、架构和学习文档；已修复失败请求幂等重放误报成功和忽略规则缺口，证据见 VERIFICATION。

完成边界：本地单用户的核心闭环可用，不代表 PostgreSQL、真实模型、容器、远程 CI 或并发已通过。候选偏好单独编辑、Embedding、checkpointer 续跑未实现。

## M2：体验修整（当前下一轮计划，尚未实施）

按实际反馈和成本推荐：

1. [UX-003](docs/PRODUCT_BACKLOG.md#ux-003)：校准字段含义与支持格式，优先修正预算空值提示。
2. [UX-001](docs/PRODUCT_BACKLOG.md#ux-001)：在既有入口/步骤说明上补首次使用与空状态的下一步。
3. [UX-002](docs/PRODUCT_BACKLOG.md#ux-002)：确认后进入档案/体验手记，失败后找到运行与适用恢复入口。
4. [UI-001](docs/PRODUCT_BACKLOG.md#ui-001)：基于稳定流程/文案打磨视觉层级、可读性和移动导航，优先级 P2；可分开交付，避免拖延 P1 验证。

验收出口：所选任务的组件/隔离 E2E 与必要人工观察有实证；生成/确认边界、Mock 标记、来源和不确定性保留。UI-001 未做时不称“视觉优化完成”；不存在虚构的用户完成率。正式陪伴素材替换 UI-002 等用户原创素材，不阻塞此阶段。

## M3：目标环境与真实 Agent 证据（计划，尚待验证）

- [INFRA-001](docs/PRODUCT_BACKLOG.md#infra-001)：PostgreSQL 迁移/回滚、schema 和现有集成测试。
- [INFRA-002](docs/PRODUCT_BACKLOG.md#infra-002)：完整 Compose/Nginx 启动、闭环与重启持久化。
- [AGENT-001](docs/PRODUCT_BACKLOG.md#agent-001)：一个兼容服务的真实 tool calling、结构/引用/约束与异常路径。
- [EVAL-001](docs/PRODUCT_BACKLOG.md#eval-001)：版本化 Prompt/工作流/案例及人工复核基线，区分规则与真实模型结果。
- [INFRA-003](docs/PRODUCT_BACKLOG.md#infra-003)：首次运行已失败；缓存父目录修复已本地验证，待用户发布后核对两个 job 和独立 PostgreSQL 集成均通过。不自动推送。

建议 PostgreSQL → 容器与真实模型 → 评测两条路径按环境独立推进，不因新增时间排序。验收出口：上述 P1 各有实际运行/复核证据；未执行、跳过和失败留在待办，配置文件存在不计完成。并发语义另由 INFRA-004 验证。

## M4 / v0.2：用证据扩展探索能力（候选，非本轮承诺）

- [AGENT-002](docs/PRODUCT_BACKLOG.md#agent-002)：多兴趣草稿与分项审批。
- [AGENT-003](docs/PRODUCT_BACKLOG.md#agent-003)：澄清后的延续请求。
- [AGENT-004](docs/PRODUCT_BACKLOG.md#agent-004)：少量有前提、可验证的轻体验模板与约束。
- [AGENT-005](docs/PRODUCT_BACKLOG.md#agent-005)：模型归纳有来源的反馈偏好候选，由用户确认；现有明确 liked_aspects 规则已完成。
- [RETR-001](docs/PRODUCT_BACKLOG.md#retr-001)：关键词与最小语义检索比较，先标注基线，不预设提升或引入大型向量基础设施。
- [DATA-001](docs/PRODUCT_BACKLOG.md#data-001)、[DATA-002](docs/PRODUCT_BACKLOG.md#data-002)、[DATA-003](docs/PRODUCT_BACKLOG.md#data-003)：数据增长后分页、导出、反馈纠错。

实施条件：真实不足案例、简单替代方案与代价评估后从 proposed 转 planned；不是必须把所有想法都做完。Prompt/检索/工作流对比复用 EVAL-001 的基线与版本规范。

## M5 / v0.3：可靠性、维护与条件性工作

- [INFRA-004](docs/PRODUCT_BACKLOG.md#infra-004)：PostgreSQL 并发审批/反馈与事务故障测试；当前 P2，在多调用者/公开场景前提高优先级。
- [DATA-004](docs/PRODUCT_BACKLOG.md#data-004)、[INFRA-005](docs/PRODUCT_BACKLOG.md#infra-005)：运行清理、审计保留和幂等请求生命周期。
- [AGENT-006](docs/PRODUCT_BACKLOG.md#agent-006)：真正的 checkpointer 恢复，当前暂缓；短流程沿用新运行安全重试。
- [UI-003](docs/PRODUCT_BACKLOG.md#ui-003)：模块化前端路由，维护/深链需求明确再做，当前暂缓。
- [UI-002](docs/PRODUCT_BACKLOG.md#ui-002)：替换正式原创陪伴 SVG，不改变核心业务模型，等待素材。
- [INFRA-006](docs/PRODUCT_BACKLOG.md#infra-006)：身份、对象权限、限流与对外部署配置，当前暂缓；对外暴露前必须拆分并提高优先级完成防护。

阶段不是硬性串行排期；跨阶段前置依赖以 Backlog 为准，不绕过依赖或用户授权。无确切需求的复杂改动继续保留，不为技术流行而实施。

## 本轮排序决策与范围

2026-10-11：在原 PostgreSQL/真实模型验证路径前，增加有用户实际反馈和源码证据的体验小迭代；首先处理预算文案，再做入口与衔接。当前没有已证实的未修 P0，未完成 P1 为 8 项，清单与理由见 Backlog。较大迭代前重新审视全部未完成任务，变化追加原因，避免路线图和正式待办维护两套状态。

2026-10-17：首次 CI 已有明确失败证据，先处理 INFRA-003 和关联的本地身份修正 INFRA-007，再回到 UX-003 → UX-001 → UX-002。两项均按 P1，其他未完成任务含 deferred 的优先级维持；没有新的业务/安全 P0 证据。INFRA-007 只完成本地身份及备份，远程仍为原 SHA；INFRA-003 仍在验收中，不能因本地测试通过标 done。

不在当前 MVP 范围：多智能体、任意网页爬取、日历同步、语音、社交、大型向量基础设施、复杂 MCP Server。不承诺未评测的准确率、性能改进或招聘结果。
