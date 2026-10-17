# 交付记录

只记录实际交付，未开始/未完成的改进见 [PRODUCT_BACKLOG](docs/PRODUCT_BACKLOG.md)，想法和决策见 [IDEA_LOG](docs/IDEA_LOG.md)，验收证据见 [VERIFICATION](docs/VERIFICATION.md)。记录日期为本地完成/复查日期，不代表 Git 提交、远程发布或版本标签；当前尚无正式发布。

## Unreleased

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
