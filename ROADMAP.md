# WonderOrbit 路线图

更新日期：2026-10-18（Asia/Shanghai）。阶段与顺序以本文件说明；正式任务的当前状态、依赖和验收只在 [PRODUCT_BACKLOG](docs/PRODUCT_BACKLOG.md) 维护，来源见 [IDEA_LOG](docs/IDEA_LOG.md)，交付见 [CHANGELOG](CHANGELOG.md)，实证见 [VERIFICATION](docs/VERIFICATION.md)。里程碑名称不代表已发布版本或 Git tag。

## 当前阶段

**M1 本地 MVP 已交付并通过 Mock + SQLite 验收；当前为 M2 的 UX-002 操作结果与流程衔接。** 2026-10-18 用户认可 UX-001 顶栏指南与双入口，结合此前整体反馈及自动化，当前范围阶段性验收，具体状态/证据只在 Backlog/VERIFICATION 维护。UX-003 的具体人工按示例记录缺口独立保留，不阻塞已授权 UX-002；不实施 UI-001，尚未进入生产或多用户验收。

本轮与历史证据分别记录于 VERIFICATION：UX-001 本地/远程与隔离浏览器已有证据，用户未报告亲测的键盘/全部空状态不冒称人工通过；本轮 UX-002 另记实际检查。本机 PostgreSQL 未配置，完整容器、PG 回滚/并发和真实模型仍待验证。

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

完成边界：本地单用户的核心闭环可用；远程 CI 已验证 PG 迁移/schema 和既有集成用例，不代表 PG 回滚/并发、真实模型或完整容器已通过。候选偏好单独编辑、Embedding、checkpointer 续跑未实现。

## M2：体验修整（当前阶段）

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
- [INFRA-003](docs/PRODUCT_BACKLOG.md#infra-003)：首次故障修复后已核对两个 Job 成功及独立 PostgreSQL 1 passed，证据见 VERIFICATION；不替代完整容器/PG 回滚验收。

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

2026-10-17（M2 首轮）：按用户明确范围恢复 UX-003 → UX-001 → UX-002 的体验顺序，先交付文案与自动化，等待用户体验反馈；CI 成功补记不扩大到完整 Docker 或 PG 回滚。其余任务优先级不变，复评与剩余 P0/P1 清单只在 Backlog 维护。以上旧日期段落保留为历史决策，不代表当前远程仍为旧 SHA。

2026-10-18（UX-001 开发轮）：从输入文案修正推进到首次使用与真实状态引导；UX-003 的人工记录缺口独立保留，获用户明确授权不阻塞 UX-001。当前先交付并等待 UX-001 首次体验，下一轮仍建议 UX-002；优先级与其他阶段顺序维持，不扩展统计、足迹重设计或真实模型。

不在当前 MVP 范围：多智能体、任意网页爬取、日历同步、语音、社交、大型向量基础设施、复杂 MCP Server。不承诺未评测的准确率、性能改进或招聘结果。

2026-10-18（UX-002 轮）：UX-001 当前范围获用户实际体验认可，按既定顺序推进 UX-002 的结果定位、精确记录导航与恢复，不改里程碑或提高其他任务优先级。UX-002 代码交付后仍需用户体验，不自动启动 UI-001、统计、足迹重设计或真实模型。
