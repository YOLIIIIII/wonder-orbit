# 实际验证记录

日期：2026-10-11（Asia/Shanghai）。所有开发和应用数据输出位于 D:\Projects\wonder-orbit。没有 git commit/push，也没有连接 Codex Cloud。未启用真实模型。

## 开发阶段记录

以下保留开发阶段的实际结果；本轮验收重跑结果单独记录在文末，不能将旧记录视为本轮重新执行。

| 检查 | 实际结果 |
| --- | --- |
| Python / 模块导入 | 项目内 Python 3.12.15，FastAPI app 导入成功 |
| uv 依赖锁 | uv lock --check --offline 成功，解析 69 包 |
| Alembic SQLite 初始化 | 在新的 .cache/release-check.db 上 upgrade head 成功 |
| Alembic schema 差异 | alembic check：No new upgrade operations detected |
| 后端 pytest | 42 passed, 1 skipped；最后执行耗时 4.50s，不作为性能基准 |
| Ruff | backend 与 evals 检查通过，代码已格式化 |
| 前端 Vitest | 3 个测试文件、9 项通过 |
| TypeScript | npm run typecheck 通过；最新 npm run build 同时执行 tsc -b |
| ESLint | 通过，包含浏览器 E2E 脚本 |
| Prettier | format:check 通过 |
| Vite 生产构建 | 成功生成 frontend/dist |
| API / 页面服务 | /api/health 返回 ok 和 mock_mode=true；前端首页 HTTP 200 |
| 浏览器闭环 | Chromium 实际通过收集→编辑草稿→批准→搜索→关联→建议接受→修改体验→反馈→候选偏好确认→运行详情 |
| 浏览器尺寸 | 1440px 桌面、390px 移动端；无 pageerror，无移动端横向溢出；截图已检查 |
| 配置文件 | Compose 与 GitHub Actions YAML 可解析；未实际执行远程 CI |

后端测试重点：未知信息留空、拒绝空步骤和无效参数、实际引用/搜索依据、未批准写入被拒、约束和当前偏好二次验证、同一审批不重复创建、请求幂等冲突、超时失败审计与重试、真实反馈持久化、候选不自动进入明确偏好、归档不推荐、UTC 时间戳。

截图位于被忽略的 .cache/e2e/：home-before.png、home-after.png、explore.png、run.png、mobile.png。截图中的兴趣和反馈由浏览器测试实际提交，保存于独立 release-check.db，属于 Mock 测试数据，未放入个人 wonder.db。

## 修复的可复现问题

- 环境 Python 3.10 / Node 16 不满足所选依赖：项目内安装 Python 3.12 / Node 22，并保留锁文件。
- 安装初始失败：沙箱限制及失效代理；经工具批准联网下载到项目缓存。
- pytest 默认临时目录访问失败：使用项目 .cache/pytest，并在所需权限下执行。
- Testing Library 缺少 DOM 同级依赖：显式补充依赖并更新锁文件。
- 搜索结果被刷新覆盖：完整档案与搜索 ID 筛选分开。
- 标签输入时尾随逗号被清除：表单保留原始输入，同时更新结构化数组。
- 编辑正式 Quest 时传入多余数据库字段：编辑器只提交 Proposal 字段。
- 反馈失败审计被 rollback 清掉：回滚后恢复失败事件并保存运行状态。
- SQLite 时区丢失：序列化时统一补 UTC。
- 浏览器测试“喜欢”标签误匹配“不喜欢”：改为 exact 选择器并复验成功。
- E2E 浏览器上下文在 ESLint 中被当作纯 Node：显式声明对应执行环境。

## 未执行与限制

- PostgreSQL 集成测试因未提供 TEST_POSTGRES_URL 跳过。没有本机 Docker / PostgreSQL，未运行完整 Compose 或 PostgreSQL 的迁移/回滚。CI 已配置，未运行远程工作流。
- 未调用真实模型或运行 live eval，不报告模型准确率、效果或真实调用速度。
- 没有多用户并发压力测试；SQLite 的并发审批语义不等于 PostgreSQL 行锁。
- 没有 checkpointer 逐节点续跑；重试是新运行安全重跑生成。
- 本次浏览器测试以开发服务器验证 UI；生产静态资源构建通过，Nginx 容器尚未运行。
- 候选偏好目前支持查看、确认和删除；可在确认后编辑明确类别，尚无候选摘要单独编辑 API。

## MVP 验收复查（2026-10-11）

本轮阅读 README、本文、LEARNING_GUIDE 和 ROADMAP，检查 Git 可提交文件、配置及 Agent 审批/异常路径。只修复可复现问题，没有增加业务功能，没有暂存、提交或推送文件。

| 本轮检查 | 实际结果 |
| --- | --- |
| 后端 pytest | 47 passed, 1 skipped（2.85s，仅记录耗时，不作为性能基准） |
| PostgreSQL 集成测试 | 跳过：未设置 TEST_POSTGRES_URL；不计入通过数 |
| Ruff lint / format | backend、evals 通过；21 个 Python 文件符合格式 |
| uv 锁文件 | uv lock --check --offline 通过，解析 69 包 |
| SQLite 迁移 | 新建独立 .cache/acceptance-<随机 ID>.db，upgrade head / current 成功，版本 0001 (head) |
| SQLite schema 差异 | alembic check：No new upgrade operations detected |
| 前端 ESLint / TypeScript | lint、typecheck 通过；使用项目内 Node 22 |
| 前端 Vitest | 3 个测试文件、9 项通过 |
| 前端构建 / 格式 | build（含 tsc -b 和 Vite）、format:check 通过 |
| PowerShell 实际解析器 | Windows PowerShell 5.1.26100.9444 与 PowerShell 7.6.5 均检查两个启动脚本，语法错误数均为 0 |
| 脚本编码 | web.ps1 为 UTF-8 with BOM；dev.ps1 全 ASCII，可供两个版本读取；本轮未修改脚本 |
| Git 忽略规则 | 用 git check-ignore 逐项验证环境文件变体、SQLite 及附属文件、虚拟环境、缓存、依赖、构建与日志被忽略；.env.example、锁文件和固定评测案例可提交 |
| 配置凭据 | .env.example 的 MODEL_API_KEY 为空；数据库用户名/密码为明确标注的本地 wonder 占位值；当前不存在 .env |
| 可提交文件扫描 | 61 个 UTF-8 文本文件未命中常见 API Key、GitHub Token、AWS Key、私钥及 Bearer Token 格式；这是限定模式扫描，不能保证识别所有可能的秘密 |
| 个人数据库 | 只检查 wonder.db 存在且被 Git 忽略，未读取其内容、迁移或写入；测试和迁移使用独立数据库 |
| Git 状态 | main 尚无提交；git ls-files --stage 为空；61 个项目文件未跟踪，无运行数据库、缓存、日志或 node_modules 出现在可提交清单 |

初次 pytest 因沙箱无法访问既有项目内 pytest 临时目录而报错，Vitest 首次启动因子进程 spawn EPERM 失败；随后在工具获准的权限下实际重跑成功。初次失败没有计入通过，也没有用修改业务代码绕过环境限制。

### 发现并修复的问题

- 原 .gitignore 未排除 .env.local 等环境变体、SQLite 的 .sqlite/.sqlite3 扩展及 journal 附属文件。补齐这些规则和轮转日志规则，显式保留 .env.example；实际个人 wonder.db 原本已经被忽略。
- 同一失败请求的幂等键重放错误返回 201，可能让前端误以为生成或反馈保存成功。新增回归测试先复现两项失败，再在 begin_run 中将失败重放改为 409，附原运行 ID 和错误类型；不重复执行模型、不增加正式记录、不覆盖失败审计。
- 新增三项模拟服务异常测试，分别验证超时、限流、不可用分类，且不将原异常详情返回给用户；没有调用真实服务。
- ROADMAP、学习指南修正候选偏好可编辑的表述；README 明确 E2E_ALLOW_WRITE 不能自动证明数据库隔离，浏览器测试前仍须核对目标服务的 DATABASE_URL。

### 审批与运行记录核对

- 草稿和候选生成只持久化 AgentRun，不创建正式 Star/Quest；批准由用户决定 API 提供，模型不能设置后端的 approved 上下文。
- 工具允许列表及 Pydantic 校验拒绝未知工具、额外参数、未经审批的正式写入。批准时重新校验引用 ID、当前偏好、时间、预算和精力；相关拒绝路径已在 pytest 中执行。
- 请求键与摘要、审批指纹、Quest 候选唯一键及 Reflection 唯一约束共同防止重复写入；已测试顺序重复提交和冲突，未证明并发压力场景。
- 节点/工具状态与耗时、运行模式/模型、公开状态快照、错误类型和结果摘要保存于 AgentRun；模型异常保存失败记录，生成重试创建新运行。未保存隐藏推理或原始服务异常消息。

### 本轮未执行

- Docker 命令不可用，未运行 Compose、Nginx 容器和 PostgreSQL 迁移/回滚；PostgreSQL 行锁及并发提交仍未验收。
- 未调用真实模型或运行 live eval，模拟服务异常通过不代表真实服务兼容性通过。
- 未运行远程 GitHub Actions；本轮未重跑浏览器 E2E 或重新启动 Web 服务，开发阶段浏览器记录保留在上文。

可创建第一个本地 MVP 提交：当前 Mock + SQLite 的规则/API 与前端检查通过，已知验收问题已修复，运行数据被忽略。此结论不代表 PostgreSQL、容器部署、真实模型或生产并发已通过验收。不要使用 git add -f 加入运行数据；未来新增测试产物也应放入被忽略的目录。

## 需求管理文档建立（DOC-001）

日期：2026-10-11（Asia/Shanghai）。本轮仅整理管理文档，没有前后端业务、脚本、依赖、数据库变更，没有执行 git commit/push 或云连接。此节与上轮应用验收分开记录。

### 范围与证据来源

- 实际阅读 README、AGENTS、ROADMAP、本文、LEARNING_GUIDE 和历史 IMPLEMENTATION_PLAN，核对 evals/README 及项目目录。
- 检查 frontend/src/App.tsx、components.tsx、styles.css，核对 backend/app/schemas.py、tools.py 的输入/验证规则与 semantic.py 预留接口。确认已有步骤提示、单草稿、空预算仍受偏好上限约束等真实行为；没有修改这些实现。
- 实际查看既有 .cache/e2e/home-after.png 与 mobile.png（2026-10-11 16:43 的历史截图），作为视觉候选方案依据；没有重新启动浏览器，也没有据此声称新设计通过验收。
- 新建 [IDEA_LOG](IDEA_LOG.md)、[PRODUCT_BACKLOG](PRODUCT_BACKLOG.md)、[CHANGELOG](../CHANGELOG.md)；更新 AGENTS、README、ROADMAP、LEARNING_GUIDE、IMPLEMENTATION_PLAN 的相关规则/导航，以及本节。历史 MVP 与验收记录继续保留。

### 实际执行的文档检查

使用项目内 Python 3.12 执行内联检查（.venv/Scripts/python.exe -c），结合 git ls-files --others --exclude-standard 和变更前 SHA-256 快照；未新增检查脚本或依赖。

| 检查 | 实际结果 |
| --- | --- |
| 唯一记录 | 12 个 IDEA ID、25 个正式任务 ID，定义不重复 |
| 任务字段和索引 | 所有任务具备统一字段，索引与详情的优先级/状态一致，值属于定义集合 |
| 双向关联 | 每条想法引用的任务存在，每个任务能回指原想法 |
| 前置依赖 | 引用的任务全部存在，依赖图无循环 |
| 文档导航 | 本轮管理文档的本地 Markdown 文件链接及稳定 ID 锚点检查通过 |
| 基本格式 | 文档可按 UTF-8 读取、标题存在，无尾随空白 |
| 修改范围 | 仅 9 个管理文档新增/修改；55 个其他原文件 SHA-256 与本轮起始快照一致，包含业务代码、脚本、锁文件和配置；未删除原文件 |
| 状态 | 仅 DOC-001 done；10 planned、10 proposed、4 deferred，无业务任务 in_progress/done，未完成 P0 为 0、P1 为 8 |
| Git | 暂存区为空、未创建提交；64 个可提交项目文件未跟踪，新增 3 个管理文档；个人 wonder.db 仍被忽略 |

检查过程中补齐 RETR 检索任务前缀的校验与 AGENTS ID 约定，复检通过；没有将第一次检查失败当作通过。DOC-001 仅在文档及修改范围检查通过后标记 done，交付记录见 CHANGELOG。

### 本轮没有执行

- 没有重跑 pytest、前端 lint/typecheck/Vitest/build 或浏览器 E2E：本轮纯文档且代码/依赖哈希未变；旧 47 passed / 1 skipped 与前端 9 passed 是历史应用验收结果。
- 没有执行 PostgreSQL、Docker、真实模型/live eval、远程 CI 或并发验证，仍由相应 P1/P2 待办跟踪。
- 没有实现流程引导、输入文案或视觉优化，也没有新的可用性/对比度测量结果；其验收条件是后续目标，不是本轮结果。

当前状态：M1 本地 MVP 基线已交付；M2 体验修整准备阶段，推荐 UX-003 → UX-001 → UX-002；工程路径保留 INFRA-001/002/003、AGENT-001、EVAL-001。正式状态/优先级以 PRODUCT_BACKLOG 为准，本节为本轮历史快照。
