# MVP 实施记录

本文保留首次 MVP 的历史检查、开发顺序和当时测试结果，不继续追加正式任务。最新进度与任务见 [PRODUCT_BACKLOG](PRODUCT_BACKLOG.md) 和 [ROADMAP](../ROADMAP.md)，后续验收见 [VERIFICATION](VERIFICATION.md)，已交付改动见 [CHANGELOG](../CHANGELOG.md)。历史测试数量不代表最新验收或本轮重跑。

## 初始检查

2026-10-11：工作目录只有 .git，无源码、提交或依赖配置。本机 Python 3.10.10、Node 16.16.0，未检测到 uv / Docker。仅操作本地项目，不访问远程 Git 或 Codex Cloud。

## 开发顺序

1. 项目内配置 uv、Python 3.12、Node 22；锁定安装成功的依赖。
2. SQLAlchemy 数据模型、Alembic 迁移、Star CRUD 与确定性检索。
3. 模型适配层、受控工具、LangGraph 节点、持久化草稿/候选/审批及运行事件。
4. 完成用户确认、反馈与可检查偏好；重复请求使用幂等键。
5. 紫色/奶油白的响应式前端，真实后端数据与明确 Mock 标记。
6. 后端确定性测试、前端组件测试/lint/类型/构建、迁移验证和端到端检查。
7. 完成中文 README、架构/学习文档和路线图；记录检查结果及限制。

## 边界

单用户本地 MVP，不做多 Agent、账号、网页爬取、日历、语音和向量数据库。PostgreSQL 为默认数据库，SQLite 仅作可复现开发/测试替代。候选持久化到 AgentRun，用户确认创建正式记录。失败运行保留审计事件，可通过独立重试 API 重新执行读取/生成流程。

## 完成记录

本地工具与锁文件、ORM/迁移、核心闭环、LangGraph/工具、应用页面、运行审计、自动化测试及中文学习文档已实现。实际验证见 VERIFICATION.md：42 项后端测试通过、1 项 PostgreSQL 测试跳过；9 项前端测试、lint、类型、格式、构建与浏览器闭环通过。PostgreSQL、完整 Compose 和真实模型仍需在具备对应环境/Key 时验证。未执行 commit、push 或远程 CI。
