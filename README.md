# WonderOrbit · 星屿
**A Personal Curiosity Agent**

给好奇心一座小小的星屿。收集零散的兴趣，发现真实的连接，再把一个想法变成轻量的小体验。个人、单用户、本地运行的 MVP；不是通用聊天机器人。

## 已实现的闭环

- Star 创建/查询/编辑/删除、类别和状态筛选、关键词搜索。所有星星查看入口默认显示只读详情，分开呈现原始文字与整理描述；点击“编辑星星”才进入表单。取消不保存，成功后展示服务端确认的最新详情，失败可继续编辑；删除仅在编辑中提供，状态仍可改为归档。
- 每次自然语言整理生成一张可编辑草稿；用户确认后写入 Star。来源区分手动、粘贴和参考链接；不抓取网页。
- 中文二元词组 / 英文词检索，返回真实 ID、原文片段、命中词和分数。关联页只展示实际共同标签或类别。
- 真实 LangGraph StateGraph：收集和探索走不同分支，调用八个经过 Pydantic 校验的受控工具。
- 根据真实星星和明确偏好生成 1–3 个候选。时间、预算、精力、引用 ID 在生成后和批准时再次验证；归档星星不参与推荐。
- 候选和草稿持久化于 AgentRun；候选属于 proposed 阶段，正式 Quest 只在确认后创建，初始状态 accepted。结果为 completed / skipped。
- 用户可修改/接受/放下候选，修改已接受体验，记录完成或未执行的真实反馈。被体验引用的星星只能归档，防止丢失依据。
- 偏好支持类别、时间、预算、精力和约束。明确偏好可编辑/删除；反馈中的明确“喜欢”形成可查看、确认或删除的候选摘要，确认后才加入明确偏好。
- 运行详情展示实际节点、工具状态、耗时、错误及结果。逐节点保存状态，生成失败可以重试；待确认结果重启后仍可从运行页打开。
- Mock 端到端，无 API Key 自动使用 Mock，并明确标注。真实服务通过 langchain-openai 的工具调用接口返回严格结构。
- 首页按已连接的真实档案区分首次收集、已有兴趣和仅有归档的情况；有未归档星星时，“收集星星”和“微型探索”并列为两个明显按钮，持续发现好奇，也让兴趣慢慢变成行动。草稿待确认/已放下/已保存含义明确，实际保存后提供档案与探索的基础入口。
- 各页顶栏刷新旁的“使用指南”打开四步说明弹窗，正文不再放置指南。可用关闭按钮、Escape 或点击遮罩关闭，键盘焦点保留在弹窗内，关闭后回到帮助入口；不自动打开，也不新增永久引导状态。
- 收集/探索的新结果渲染且处理中状态结束后，一次性定位到本轮草稿、候选或澄清；尊重减少动画偏好，切页或打开弹窗时不抢焦点。保存后“查看这颗星星”按真实 ID 读取并打开只读详情、清除会隐藏目标的搜索/筛选；首页/档案卡片、轨道和探索引用也默认阅读。未知时间/预算/精力显示“尚未记录”，明确 0 元仍为零；参考链接仅 http/https 可点击。接受候选后“查看这次体验”仍按 quest_id 定位手记卡片，不自动填写反馈。
- 失败提示关联真实 run_id，可查看足迹详情；仅无决定的 failed 生成提供安全重试，返回新运行、保留原失败，不自动审批。running 不猜测超时或绕过后端保护；刷新后可从足迹重新读取并打开真实待确认结果，只有澄清时显示“查看澄清提示”。
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
if (-not (Test-Path -LiteralPath '.env')) { Copy-Item .env.example .env }
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

本机没有可用 Docker / PostgreSQL，完整容器启动和 PostgreSQL 集成尚未在本机验证。[首次 GitHub Actions](https://github.com/YOLIIIIII/wonder-orbit/actions/runs/38140512844) 的前端、PostgreSQL 迁移/schema 检查通过，但普通 pytest 因缺少 .cache 父目录失败，后续独立 PostgreSQL 集成步骤未执行。2026-10-17 修复后的 [GitHub Actions](https://github.com/YOLIIIIII/wonder-orbit/actions/runs/39030090153) 两个 Job 均 success，独立 PostgreSQL 集成实际 1 passed；完整 Compose/Nginx、PG 回滚与并发仍未完成验收。

## 模型配置

在被忽略的 .env 中配置，勿填写到源码或 .env.example：

| 环境变量 | 说明 |
| --- | --- |
| DATABASE_URL | 默认 PostgreSQL；SQLite 开发替代为 sqlite:///./wonder.db |
| MOCK_MODE | 默认 true；设为 false 且有 Key 才启用真实模型；本阶段保持 true |
| MODEL_PROVIDER | 新增供应商选择，默认 openai-compatible；百炼填 bailian，只对 qwen3.8-flash 添加非思考参数 |
| MODEL_API_BASE_URL | 支持 OpenAI 格式的服务地址，通常以 /v1 结尾 |
| MODEL_API_KEY | 默认空，缺少 Key 时明确回退到 Mock |
| MODEL_NAME | 服务支持的模型名；示例 gpt-4o-mini 是配置占位 |
| MODEL_TIMEOUT | 单次调用超时秒数，默认 30 |
| MODEL_MAX_RETRIES | 日常默认 1；受限 Live runner 必须为 0，避免隐式追加请求 |
| MODEL_MAX_TOKENS | 输出 Token 配置，默认 2048；锁定 LangChain 实际发送 max_completion_tokens |
| CORS_ORIGINS | 允许的前端来源，逗号分隔 |

真实服务需支持 chat completions、function/tool calling、指定 tool_choice 和所用模型的 max_tokens 参数。不同“兼容”服务仍可能存在差异。输出通过 Pydantic 校验，超时、限流、不可用、非法工具/结构记录为失败，不能静默当作成功。用户已在百炼准备北京地域 Key/Host、免费额度和用完即停（用户确认，助手未读取或联网核验）。2026-10-25 只完成 Qwen3.8-Flash 接入准备与离线兼容测试，所有真实模型检查 not run；配置及下一阶段受限命令见 [evals](evals/README.md)。

本地北京配置：API Key 是私有鉴权凭据；API Host 是业务空间专属域名；Base URL 是 `https://{实际APIHost}/compatible-mode/v1`；Model ID 填 `qwen3.8-flash`。仅在本地 .env/环境变量填真实 Key/Host，不覆盖已有 .env、不贴到对话或 GitHub，.env.example 只放公开占位；继续 `MOCK_MODE=true`。未来真实请求前才按明确授权设置非 Mock 与 `MODEL_MAX_RETRIES=0`。

原 `bind_tools(..., tool_choice=tool_name)` 会变成指定函数对象；百炼 Qwen 的思考模式对该策略有限制，因此仅 `MODEL_PROVIDER=bailian` 且型号精确匹配时传 `extra_body={"enable_thinking": false}`。保留唯一工具与 Pydantic、来源/未知值、审批和幂等校验，不接受普通文本。离线测试用实际 LangChain/SDK 序列化加内存传输，验证最终 JSON，并不调用模型。下一阶段另获授权后才运行 `evals/run_live.py --allow-live --max-cases 1`：最多一个公开 collect、失败停跑、无 SDK 重试、无数据库写入；可能消耗输入/输出 Token，只保留真实 SDK usage，缺失为 null。完整初学者步骤与边界见 [evals/README](evals/README.md)。

2026-10-25 第二阶段新增隔离工作流入口 `evals/run_workflow_live.py --allow-live`：最多 collect/explore 各一次、零重试，通过现有 FastAPI/图/工具和模拟测试 decision，所有正式测试数据仅在新建 .cache SQLite；实际 engine/迁移/初始零记录检查先于模型，默认 pytest/CI 不执行。**本轮已运行一次 collect 后停止**：工具/结构/图生成通过，interest_reason 将主题复述为动机，严格空值检查失败；没有批准、没有 Star/Quest/Reflection，没有发起 explore。真实用量 1245 Token；后续新调用须另获授权，不使用本轮剩余次数补跑。入口/离线命令和边界见 [evals](evals/README.md)，[真实证据](docs/VERIFICATION.md#agent-001-workflow-20261025)；不是完整 Agent 闭环成功。

Mock 草稿不会猜测兴趣原因、预算或精力。免费“写三个好奇问题”体验预算为 0，时间明确为估计值。约束取当前请求与已设置偏好的较严格上限。预算受限时未知预算会被拒绝；自由文本约束不会让模型自行宣称满足。

## 输入提示与实际规则

微型探索与我的偏好默认显示简短提示；点击“查看…规则”，或用键盘 Tab 定位后按 Enter/空格，可展开和收起完整说明。草稿里“尚不清楚”的中文项目表示信息待补充，可选项可留空，并非整理出错。

- 每次收集围绕一个兴趣，先填写原始文字；参考链接只保存来源，接受完整 http/https 地址，不读取网页。整理只生成一张草稿，确认后入档。
- 本次预算 0 是明确零预算；留空仍遵守偏好预算上限，都未设置则不额外限制，同时设置取更低上限。未知预计预算留空，不等于免费；有上限时未知成本不能通过检查。
- 时间为分钟（1–1440）：预计时间指所需时长，本次可用时间是上限（可选，留空沿用偏好最长时间）；仍需符合偏好最短/最长范围，冲突会澄清。精力按低/中/高取较低上限；未知或未设置不代表低精力。
- 标签、类别、约束、喜欢/不喜欢列表支持中英文逗号及换行解析；当前单行框建议逗号。步骤和不确定性一行一项。未知兴趣原因可留空，无需猜测；必填及范围见字段附近说明。
- 自由文本约束目前只支持原词“仅室内”“不购买”“不外出”，限定免费室内文字记录体验；其他约束需澄清，不代表模型能自动验证。

## 检查与测试

```powershell
New-Item -ItemType Directory -Path .cache -Force | Out-Null
uv run pytest -q
uv run ruff check backend evals
uv run ruff format --check backend evals
uv run alembic check
cd frontend
npm run format:check
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

浏览器测试覆盖空档案首次引导、待确认、拦截模拟保存失败、真实放下/批准、保存后基础导航不重复写入，以及搜索/关联、5 元偏好下空预算与 0 元、探索/修改/反馈/偏好/足迹闭环；检查八个页面在 1440px 与 390px 的顶栏指南、三种关闭方式与键盘焦点，并检查首页双按钮大小/权重及导航不增加 Star/Quest。探索/偏好的字段帮助仍按需展开。截图保存在 .cache/e2e，并包含明确由测试输入/批准形成的数据。脚本只检查 E2E_ALLOW_WRITE 授权，不会自动核验后端数据库地址；执行前必须确认目标服务使用专用临时数据库，否则可能写入个人档案。

实际检查结果和未执行项见 [验证记录](docs/VERIFICATION.md)。

UX-002 的追加浏览器检查在 e2e/results.mjs，由 smoke.mjs 调用，覆盖双尺寸结果定位、普通 Tab、减少动画、刷新恢复、切页取消、Star/Quest 精确 ID 与写入计数。默认不注入后端故障；只在已核验的专用启动器对文本 `UX002-E2E-FAIL-` 提供一次性 Mock timeout 时设置 E2E_INJECTED_FAILURE=true，才执行真实失败 run_id 与 retry 段，否则明确输出 SKIP。不在日常服务或真实模型上启用故障注入。本轮实际隔离启动器、数据库路径与重试证据见 VERIFICATION。

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

2026-10-25：M1 本地 MVP 已交付；M2 的 UX-001/002 验收保留，UX-003 人工记录缺口与 UI-001 仍保留。M3 已推进 AGENT-001 第二阶段：用户已报告适配器 collect-only 成功，本轮一次真实 API/图 collect 因动机字段语义不满足而在批准前停止，explore/正式审批仍待验证。AGENT-001 保持 in_progress；PG 回滚/并发、完整 Docker 与 EVAL 基线未完成，下一步先明确主题/动机的离线规则，不自动增加真实调用。正式状态只在 Backlog 维护。

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

2026-10-17 已核对远程 main 的 CI 修复基线 172103d，Author/Committer 为 GitHub noreply 身份。历史身份修正、旧失败和后续成功证据分别保留在 [验证记录](docs/VERIFICATION.md)；本轮仅按用户授权普通推送，不改写远程历史，未连接 Codex Cloud。
