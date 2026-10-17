# WonderOrbit · 星屿
**A Personal Curiosity Agent**

给好奇心一座小小的星屿。收集零散的兴趣，发现真实的连接，再把一个想法变成轻量的小体验。个人、单用户、本地运行的 MVP；不是通用聊天机器人。

## 已实现的闭环

- Star 创建/查询/编辑/删除、类别和状态筛选、关键词搜索。保留原始文字和独立结构化字段。
- 自然语言整理为可编辑草稿；用户确认后写入 Star。来源区分手动、粘贴和参考链接；不抓取网页。
- 中文二元词组 / 英文词检索，返回真实 ID、原文片段、命中词和分数。关联页只展示实际共同标签或类别。
- 真实 LangGraph StateGraph：收集和探索走不同分支，调用八个经过 Pydantic 校验的受控工具。
- 根据真实星星和明确偏好生成 1–3 个候选。时间、预算、精力、引用 ID 在生成后和批准时再次验证；归档星星不参与推荐。
- 候选和草稿持久化于 AgentRun；候选属于 proposed 阶段，正式 Quest 只在确认后创建，初始状态 accepted。结果为 completed / skipped。
- 用户可修改/接受/放下候选，修改已接受体验，记录完成或未执行的真实反馈。被体验引用的星星只能归档，防止丢失依据。
- 偏好支持类别、时间、预算、精力和约束。明确偏好可编辑/删除；反馈中的明确“喜欢”形成可查看、确认或删除的候选摘要，确认后才加入明确偏好。
- 运行详情展示实际节点、工具状态、耗时、错误及结果。逐节点保存状态，生成失败可以重试；待确认结果重启后仍可从运行页打开。
- Mock 端到端，无 API Key 自动使用 Mock，并明确标注。真实服务通过 langchain-openai 的工具调用接口返回严格结构。
- React 页面：首页、收集、档案、关联、探索、体验手记、Agent 足迹、偏好。原创 SVG 星球和可替换 CSS 陪伴形象，紫色/暖黄/奶油白布局。

Mock 使用固定主题词和免费的文字记录模板，不具备大模型语义理解能力；完整闭环仍使用真实数据库和真实 LangGraph。

## 快速启动：当前 Windows 工作目录

本次已在项目的忽略目录中安装 Python 3.12、uv、Node 22 和依赖。系统原有 Node 16 不兼容当前前端。下面脚本优先使用项目内工具。

终端一，在仓库根目录：

```powershell
cd D:\Projects\wonder-orbit
.\scripts\dev.ps1 -Sqlite
```

终端二，在仓库根目录：

```powershell
.\scripts\web.ps1
```

打开 [应用](http://127.0.0.1:5173) 和 [后端 API 文档](http://127.0.0.1:8000/docs)。首次档案为空，不自动放入演示数据。SQLite 数据保存于被忽略的 wonder.db；所有表通过 Alembic 初始化。若 PowerShell 执行策略限制脚本，可仅为此次启动使用 `powershell -ExecutionPolicy Bypass -File .\scripts\dev.ps1 -Sqlite`，前端同理。

## 标准开发环境：PostgreSQL

需要 uv、Python 3.12、Node 22.13+ 和 Docker Compose。

```powershell
# 仅首次创建 .env；已有配置时不要覆盖
Copy-Item .env.example .env
uv sync --frozen --python 3.12
docker compose up -d db
$env:PYTHONPATH='backend'
uv run alembic upgrade head
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

另一终端：

```powershell
cd frontend
npm ci
npm run dev
```

Linux/macOS 将 `$env:PYTHONPATH='backend'` 换成 `export PYTHONPATH=backend`。完整容器启动：创建 .env 后执行 `docker compose up --build`，应用在 [localhost:8080](http://localhost:8080)，后端自动执行迁移。数据库持久化到 wonder_data volume。默认开发数据库密码仅供本机使用；端口绑定 127.0.0.1。

本机没有可用 Docker / PostgreSQL，完整容器启动和 PostgreSQL 集成尚未在本机验证。[首次 GitHub Actions](https://github.com/YOLIIIIII/wonder-orbit/actions/runs/38140512844) 的前端、PostgreSQL 迁移/schema 检查通过，但普通 pytest 因缺少 .cache 父目录失败，后续独立 PostgreSQL 集成步骤未执行。2026-10-17 已在本地修复并复现验证；修复后的远程 CI 尚待用户发布后验收，不能宣称全绿。

## 模型配置

在被忽略的 .env 中配置，勿填写到源码或 .env.example：

| 环境变量 | 说明 |
| --- | --- |
| DATABASE_URL | 默认 PostgreSQL；SQLite 开发替代为 sqlite:///./wonder.db |
| MOCK_MODE | 默认 true；设为 false 且有 Key 才启用真实模型 |
| MODEL_API_BASE_URL | 支持 OpenAI 格式的服务地址，通常以 /v1 结尾 |
| MODEL_API_KEY | 默认空，缺少 Key 时明确回退到 Mock |
| MODEL_NAME | 服务支持的模型名；示例 gpt-4o-mini 是配置占位 |
| MODEL_TIMEOUT | 单次调用超时秒数，默认 30 |
| MODEL_MAX_RETRIES | SDK 重试次数，默认 1 |
| MODEL_MAX_TOKENS | 输出 token 上限，默认 2048 |
| CORS_ORIGINS | 允许的前端来源，逗号分隔 |

真实服务需支持 chat completions、function/tool calling、指定 tool_choice 和所用模型的 max_tokens 参数。不同“兼容”服务仍可能存在差异。输出通过 Pydantic 校验，超时、限流、不可用、非法工具/结构记录为失败，不能静默当作成功。当前没有真实 Key，未验证任何真实模型服务或调用费用；可选评测见 [evals](evals/README.md)。

Mock 草稿不会猜测兴趣原因、预算或精力。免费“写三个好奇问题”体验预算为 0，时间明确为估计值。约束取当前请求与已设置偏好的较严格上限。预算受限时未知预算会被拒绝；自由文本约束不会让模型自行宣称满足。

## 检查与测试

```powershell
New-Item -ItemType Directory -Path .cache -Force | Out-Null
uv run pytest -q
uv run ruff check backend evals
uv run alembic check
cd frontend
npm run lint
npm run typecheck
npm test
npm run build
```

本机用已安装工具也可以运行 `.\.venv\Scripts\python.exe -m pytest -q`；前端先将项目的 Node 22 bin 加入当前终端 PATH，或直接使用它启动 node_modules 下的 CLI。

- 后端测试使用隔离 SQLite 数据库；临时文件在 .cache/pytest。pytest 的 basetemp 不自动创建父目录，全新检出必须先创建 .cache；CI 也在 pytest 前执行 mkdir -p .cache。设置 uv 的外部下载缓存不等于创建这个测试目录。
- 设置 TEST_POSTGRES_URL 后，test_postgres.py 在独立临时 schema 中检查 PostgreSQL JSON 和外键保护。
- 固定兴趣提取案例在 evals/cases.json；规则测试与真实模型评测分开。
- 可复现浏览器流程在 frontend/e2e/smoke.mjs。必须对专用临时数据库运行；E2E_ALLOW_WRITE=true 明确允许写测试数据，不能用于个人正式档案。先将后端 DATABASE_URL 设为 sqlite:///./.cache/e2e.db，迁移并启动后端，启动前端，再运行：

```powershell
cd frontend
npx playwright install chromium
$env:E2E_ALLOW_WRITE='true'
npm run test:e2e
```

浏览器测试覆盖收集、确认、搜索、关联、探索接受、修改、反馈、偏好确认和运行详情，同时检查 390px 布局。截图保存在 .cache/e2e，并包含明确由测试输入/批准形成的数据。脚本只检查 E2E_ALLOW_WRITE 授权，不会自动核验后端数据库地址；执行前必须确认目标服务使用专用临时数据库，否则可能写入个人档案。

实际检查结果和未执行项见 [验证记录](docs/VERIFICATION.md)。

## 依赖与模块

实际安装的主要版本：Python 3.12.15、uv 0.13.0、FastAPI 0.143.0、Pydantic 2.14.0、LangGraph 1.2.14、langchain-openai 1.7.0、SQLAlchemy 2.1.4、Alembic 1.20.0、psycopg 3.3.6、pytest 9.1.1、Uvicorn 0.54.0；Node 22.23.3、React 19.3.0、TypeScript 5.8.3、Vite 6.4.4、Vitest 3.2.7、ESLint 9.39.5。完整精确依赖由 uv.lock / frontend/package-lock.json 锁定。接口与安装组合经过本地导入、测试和构建验证。

```text
backend/
  app/           API、配置、ORM、结构校验、检索、模型适配、工具和图
  migrations/    Alembic 初始迁移
  tests/         业务、安全边界和可选 PostgreSQL 集成
frontend/
  src/           页面、可编辑表单、SVG、样式、API 和组件测试
  e2e/           真实浏览器闭环
evals/           固定案例与可选真实模型运行器
docs/           架构、学习指南、开发计划与验证记录
scripts/        当前 Windows 环境启动脚本
.github/        CI
```

学习建议：先读 [学习指南](docs/LEARNING_GUIDE.md)，再读 schemas.py → workflow.py → tools.py → model_adapter.py → models.py → main.py → test_mvp.py。[架构](docs/ARCHITECTURE.md) 解释事务、审批和持久化边界；[路线图](ROADMAP.md) 区分后续阶段。

## 持续迭代记录

- [想法与决策](docs/IDEA_LOG.md)：保留用户反馈、来源、候选方案和暂缓/拒绝原因。
- [产品待办](docs/PRODUCT_BACKLOG.md)：稳定任务 ID、优先级、状态、依赖和验收标准，是正式任务的维护入口。
- [路线图](ROADMAP.md)：当前阶段与里程碑；[交付记录](CHANGELOG.md) 只记实际完成的改动；[验证记录](docs/VERIFICATION.md) 区分通过、跳过和未执行。
- [开发约定](AGENTS.md)：开始开发前读取和复评记录，结束后同步状态与实证。

当前本地 MVP 闭环已经交付，Mock + SQLite 的本轮回归通过；当前优先收尾 INFRA-003 的 CI 故障验证，再恢复输入提示和流程衔接队列。三项体验反馈尚未实现；PostgreSQL 集成、真实模型、Docker 和修复后的远程 CI 仍待验证。列表中的 planned 不是已经实施，也不授权远程推送或模型调用。

## 已知限制

- 单用户本地 MVP，没有登录、权限隔离或互联网部署防护。默认只监听回环地址。
- 检索是可解释的字面匹配：最多返回 20 条，中文使用二元词组。关联计算按配对遍历；未实现 Embedding、语义索引或分页。
- 每次收集生成一张草稿；尚未拆分多个兴趣。Mock 是规则演示，不代表真实模型效果。
- 可确定性验证的自由文本约束仅为“仅室内、不购买、不外出”的固定文字记录步骤。其他约束先要求澄清，未实现通用约束语义判断。
- 个性化排序只使用明确类别；历史反馈尚不做模型归纳，只从用户明确填写的喜欢形成候选摘要。它们不会自动成为事实。
- SQLite 仅供开发与规则测试；PostgreSQL 使用审批行锁和关系外键。SQLite 不保证多个并发审批者的锁行为，MVP 不面向多用户并发。
- 节点快照与待审批结果可以恢复查看；生成失败重试会新建运行，重新执行安全的读取/生成，不做 LangGraph checkpointer 的逐步续跑或后台驻留。进程中断的 running 记录需等待保护期后调用 retry。
- 每个 Quest 仅记录一次最终反馈；结果保存后不再编辑。模型生成的说明仍需用户核对，尚无自动文本事实核查。
- 没有网页爬取、日历、语音、社交、多 Agent 或 MCP Server。没有宣称模型准确率、性能提升或任务成功率。

2026-10-17 已按授权仅在本地备份并 amend 根提交的 Author/Committer，未推送远程；CI 修复尚未提交。身份、历史改写和安全发布步骤见 [验证记录](docs/VERIFICATION.md) 的本轮章节；未连接 Codex Cloud。
