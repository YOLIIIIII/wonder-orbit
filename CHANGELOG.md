# 交付记录

只记录实际交付，未开始/未完成的改进见 [PRODUCT_BACKLOG](docs/PRODUCT_BACKLOG.md)，想法和决策见 [IDEA_LOG](docs/IDEA_LOG.md)，验收证据见 [VERIFICATION](docs/VERIFICATION.md)。记录日期为本地完成/复查日期，不代表 Git 提交、远程发布或版本标签；当前尚无正式发布。

## Unreleased

### 2026-10-17：M2 首轮输入文案交付（UX-003）与 CI 证据收尾

- 探索预算分开字段名和辅助说明，解释 0、空值、偏好上限与较严格限制；时间、精力说明对齐后端，可用时间允许留空沿用偏好最长时间。
- 收集示例聚焦深海生物发光，明确每次一张可编辑草稿、确认后入档；参考链接用完整示例，说明只保存来源、不读取网页、仍需原始文字，表单限定 http/https。
- 标签、类别、约束、反馈统一支持格式说明；步骤/不确定性一行一项；未知原因/预算/精力可空。补齐现有 Schema 的 HTML 长度/数值边界和必填/可选提示；辅助文字 14px、关联输入，保留紫色/奶油白/暖黄布局。
- 增加组件与 5 元偏好预算 API 回归，更新原有浏览器脚本的标签与检查范围；本地后端 52 passed / 1 skipped，前端 17 passed，格式/lint/类型/build 通过，隔离浏览器闭环及三页 1440/390px 检查通过。真实失败与环境重试见 VERIFICATION。
- 同步 IDEA-002、Backlog、README、导航和里程碑；核对上一轮 CI 39030090153 两个 Job success、独立 PG 1 passed，收尾 INFRA-003，完整 Docker/PG 回滚仍待验证。
- 本节只记录代码和自动化交付；UX-003 的用户人工体验尚未验收，状态仍由 Backlog 维护。不实施 UX-001/002 或 UI-001。

### 2026-10-17：提交身份与 CI 本地修复（INFRA-007 / INFRA-003）

- 已交付 INFRA-007 的本地范围：只配置仓库 GitHub 姓名/邮箱；备份唯一根提交后 amend --reset-author，Author/Committer 均正确，新旧文件树相同。远程历史未推送，备份引用保留。
- CI 在 pytest 前新增 mkdir -p .cache，解决全新检出缺父目录的 setup 错误；未修改测试、Agent、数据模型、前端或依赖。
- 独立干净检出先复现 12 passed / 1 skipped / 35 errors，只补父目录后 47 passed / 1 skipped；根目录回归同样通过，Ruff、隔离 SQLite 迁移/schema、前端 npm ci/格式/lint/类型/9 项测试/build 通过。
- INFRA-003 尚未完成远程验收：原始运行 frontend 成功、backend 失败、独立 PG 集成步骤 skipped；修复未提交/推送，本机缺 PG/Docker。命令、原失败链接和带 lease 的待确认发布步骤见 VERIFICATION。

### 2026-10-11：需求与迭代维护机制（DOC-001）

- 建立 IDEA_LOG 和 PRODUCT_BACKLOG，录入三项用户体验反馈及旧路线图工作，关联稳定 ID、优先级、状态、依赖、风险和验收条件。
- 增加本交付记录；更新 AGENTS 的迭代维护规则、ROADMAP 的阶段/顺序和 README 导航；历史实施记录继续保留。
- 体验引导、提示文案和视觉任务仍未实施；本轮仅交付文档，不变更业务代码、脚本、依赖或数据库。
- 验收：文档关联/任务字段/依赖/状态与修改范围检查，结果见 VERIFICATION 的“需求管理文档建立（DOC-001）”章节；应用自动化测试未在本轮重跑。

### 2026-10-11：既有 MVP 与验收修复（历史回填）

- 已交付本地 Star 管理、单草稿确认、关键词关联检索、LangGraph/受控工具、体验审批、真实反馈、明确/候选偏好、Mock 和运行记录，以及对应 React 页面、配置、测试与中文学习文档。
- 已修复失败幂等请求重放误报 201：改为 409 并附原 run_id，增加回归及模拟服务异常分类测试。
- 已补齐环境文件变体、SQLite 附属文件和轮转日志的 Git 忽略规则，并纠正文档能力表述。
- 最近应用验收：后端 47 passed / 1 skipped（PostgreSQL 未配置），前端 9 passed 与 lint/typecheck/build/格式通过；细节与更早浏览器证据保留在 VERIFICATION。
- PostgreSQL、真实模型、完整容器和远程 CI 的实际验收仍未完成；上述配置和适配代码已存在，不能把历史回填当成本轮新增功能。
