# WonderOrbit 逐文件项目导航手册

核对日期：2026-10-11（Asia/Shanghai）。以本轮实际文件与源码为准，适合有 Java 后端基础、初学 Python Agent 的读者。本文解释“在哪里、怎么连起来、改完检查什么”，不另建需求或测试成绩台账。

局部更新：2026-10-17 同步 UX-003 输入规则与浏览器选择器、CI 成功证据边界。未增删重要源码文件，也未改变模块职责、API、启动命令或数据流；ListInput 增加可访问标签及说明关联参数，原 split 解析保持不变。下文“本轮”和第八节首次导航检查数据保留为 2026-10-11 历史记录；最新实际执行结果见 [VERIFICATION](VERIFICATION.md) 的 UX-003 章节。

2026-10-11 首次导航编写时只允许创建本手册、补充 AGENTS；因此未改 Backlog/CHANGELOG/VERIFICATION。本文的当前状态是带日期的快照，正式任务仍以 [PRODUCT_BACKLOG](PRODUCT_BACKLOG.md) 为准，测试证据以 [VERIFICATION](VERIFICATION.md) 为准。历史 47 passed / 1 skipped 与前端 9 passed 不能当作本轮重跑结果。

阅读范围为自有源码、测试、脚本、文档及配置/锁文件元数据；忽略 .git 内部、node_modules、.venv、.tools、.cache、dist 等第三方/运行产物。没有读取个人数据库内容或真实私有配置。当前检查范围内文件用途均可从内容确认；未来无法确认的新文件须标“待核实”，不能根据文件名填功能。

2026-10-18 局部更新：UX-003 将探索/偏好的完整填写规则放入原生 details/summary，默认保留关键短提示；App 内 draftFieldNames 只映射草稿 missing_fields 的展示（未知 key 用通用中文），不改变底层数据或审批。样式仅新增 .form-help 与 .draft-fields，未调整页面职责、启动命令或调用链；浏览器脚本增加 Enter/Space/点击与展开后窄屏检查。五项真实用户反馈及未来候选由 IDEA_LOG/Backlog 跟踪，本手册不另列待办。

2026-10-18（UX-001）局部更新：App 内新增 UsageGuide 与 SavedStarNextStep，分别负责可重开内联四步说明、实际保存后的普通导航；首页依据 refresh 成功后的真实 stars 及归档状态，结果依据 Run 状态/决定和返回 ID。generate 开始新收集时清除旧成功展示，手动保存与审批成功后才显示下一步。API、后端、Schema、启动命令保持不变；不加入自动滚动/深链/跨页审批恢复。App.test 与 smoke.mjs 覆盖这些状态，验证证据和三问复盘见 VERIFICATION；AGENTS 新增每轮三问约定。

2026-10-18（UX-001 人工反馈修正二）局部更新：UsageGuide 现在仅负责四步/模式说明内容，由 App 的 guideOpen 临时状态和所有页面共用的顶栏“使用指南”按钮打开既有 Modal；正文原内联指南已移除。Modal 沿用焦点循环、Escape/关闭/遮罩关闭与焦点恢复，CSS 约束网格列以防窄屏被 650px 固定宽度撑出。home 的 hero-actions 在有未归档 Star 时展示两个同尺寸按钮；无连接/无正式 Star/仅归档及保存后的状态逻辑不变，按钮仍只 setPage。未新增重要源码文件、依赖、API、Schema 或持久化；App.test 与 smoke.mjs 覆盖八页、模式/状态、键盘与双尺寸浏览器行为。历史内联方案见上段，最新证据及三问复盘见 [修正二验证](VERIFICATION.md#ux-001-feedback2-20261018)。

2026-10-18（UX-002）局部更新：App 的 setPage 维护本次页面导航序号，generate/presentRun/restoreRun/retryRun 以真实 run_id 提交一次性 focusTarget，useEffect 等 DOM 与 busy 结束后聚焦/滚动，切页取消、有 Modal 时丢弃定位，减少动画时使用 auto。viewStar 读取 /stars/{id}、清除过滤后打开现有 Modal；StarCard 有稳定 DOM ID，跨页 Modal 关闭后回到对应卡片。viewQuest 使用现有 /quests 按 quest_id 核对后定位手记，不新增反馈或路由。refresh 同步服务器决定，对仍在查看但不在最近 50 项列表中的运行额外按 ID 读取；失败提示保留 run_id，恢复和 retry 前再次 GET 核对。running 不猜后端超时，重试限无决定的 failed 生成，不改变后端规则/Schema/依赖。

新增 App.results.test.tsx 专门测试结果/焦点/ID/恢复边界，test-setup.ts 仅补 JSDOM scrollIntoView mock；新增 e2e/results.mjs 由 smoke.mjs 调用，负责真实双尺寸定位、恢复、精确导航及计数检查。可选 E2E_INJECTED_FAILURE=true 只用于带一次性 Mock timeout 的隔离启动器；没有该 fixture 时明确跳过故障段，正常闭环继续。新增文件职责与执行证据见下表及 [UX-002 验证](VERIFICATION.md#ux-002-20261018)；不加入新工作流、工具、checkpointer 或模型。

2026-10-18（UX-002 查看/编辑分离）局部更新：components.tsx 新增 StarDetails 只读展示真实 Star，原文/描述分开、未知值与 0 元区分，链接仅 http/https 可点击，正文普通 React 文本。App 的 selectedStar 统一默认阅读，starEditing 明确选择才挂载原 StarEditor；取消卸载草稿无写入，PUT 成功核对返回 id 并展示服务端内容，失败保留表单，删除仅在编辑内。viewStar(id, navigate) 支持精确档案跳转和来源原页阅读；异步前捕获 starOpener，Modal 用 returnFocusTo/卡片 ID 恢复焦点，Tab 循环纳入链接。编辑/阅读切换聚焦表单标题输入或详情标题，关闭途中到达的旧保存响应不重开弹窗。未新增文件、API、Schema、依赖或 Quest 行为；App.results/components 测试与 results/smoke 浏览器同步。历史“默认编辑弹窗”由本轮只读详情替代，实证见 [本轮验证](VERIFICATION.md#ux-002-star-reading-20261018)。

2026-10-25（AGENT-001 第一阶段）局部更新：新增 test_qwen_adapter.py 和 test_live_runner.py，模型/runner 行为及未来 Live 命令如下表同步。Settings 只新增 MODEL_PROVIDER，适配器仅对百炼 qwen3.8-flash 传 extra_body.enable_thinking=false，并固定 Chat Completions；last_usage 仅保留 SDK 实际三项 Token 计数。runner 不再强制覆盖 Mock，默认最多一个公开 collect，预检/零重试/失败停跑；不导入数据库。测试 conftest 在导入应用前禁用 .env 与 tracing；测试中的授权字符串只驱动 Fake，不执行真实 Live 命令。API、图、八个受控工具、审批/幂等/来源与数据库结构均未改变，无迁移/依赖变更。下文首次文件数与静态核验为带日期历史，不代表本轮重新统计；本轮实证见 [VERIFICATION](VERIFICATION.md#agent-001-phase1-20261025)。

2026-10-25 CI 复验追加：既有 App.results.test.tsx 的多 Quest 导航用例由立即焦点断言改为等待 useEffect 实际设置焦点；保留原 ID/焦点/写入次数要求，非业务/路由/模块职责变化。原手册 B/Q/F 命令仍适用，首轮失败及真实重跑见 VERIFICATION。

## 一、整体地图与阅读入口

```text
wonder-orbit/
├─ README.md / AGENTS.md / ROADMAP.md / CHANGELOG.md
├─ pyproject.toml / uv.lock            Python 依赖及检查规则
├─ .env.example / alembic.ini          环境示例及迁移入口
├─ docker-compose.yml                 db + backend + frontend
├─ .gitignore / .dockerignore
├─ backend/
│  ├─ app/
│  │  ├─ main.py                      FastAPI 入口与用例编排
│  │  ├─ schemas.py                   Pydantic DTO / 工具参数
│  │  ├─ workflow.py                  StateGraph / 节点审计
│  │  ├─ tools.py                     允许工具 / 验证 / 写入守卫
│  │  ├─ model_adapter.py             Mock / 真实服务适配
│  │  ├─ models.py / db.py / config.py ORM / Session / 配置
│  │  └─ retrieval.py / semantic.py / rules.py
│  ├─ migrations/                     env + 模板 + 0001 初始迁移
│  ├─ tests/                          隔离 SQLite / 可选 PostgreSQL
│  └─ Dockerfile
├─ frontend/
│  ├─ index.html                      DOM 根节点
│  ├─ src/main.tsx → App.tsx           React 挂载 → 八个页面
│  ├─ src/components.tsx / styles.css  编辑器、展示组件和样式
│  ├─ src/api.ts / types.ts            fetch 包装 / 编译期契约
│  ├─ src/*.test.ts* / test-setup.ts    组件和请求层测试
│  ├─ e2e/smoke.mjs → results.mjs     隔离库闭环 → 结果定位/精确导航/恢复
│  ├─ package.json / package-lock.json / vite.config.ts
│  └─ tsconfig.json / eslint.config.js / Dockerfile / nginx.conf / .dockerignore
├─ scripts/dev.ps1 / web.ps1           Windows 启动入口
├─ evals/                             固定案例与可选 Live 评测
├─ docs/                              导航、架构、学习、管理、证据
└─ .github/workflows/ci.yml            已配置的远程检查
```

最值得先读的五个源码：**schemas.py → workflow.py → tools.py → model_adapter.py → main.py**（均在 backend/app）。先学契约，再追图/工具，最后看 HTTP 如何控制审批和事务；随后读 models.py/db.py 学数据落库，读 test_mvp.py 看行为断言，读 App.tsx 看用户如何确认。

Java 对照：Pydantic 类近似 DTO + Bean Validation，FastAPI Depends 近似注入，SQLAlchemy Session 近似事务工作单元，Alembic 近似结构迁移工具。TypedDict 描述图状态，不自动替代运行时 Pydantic 校验；TypeScript 类型也不自动校验 HTTP JSON。

## 二、文档索引

| 路径 | 记录什么 | 什么时候更新 |
| --- | --- | --- |
| [README.md](../README.md) | 产品定位、实际能力、安装/启动/配置/已知限制 | 对外说明、启动方式或能力边界实际变化时 |
| [AGENTS.md](../AGENTS.md) | 开发范围、审批真实性、测试和迭代维护规则 | 开发约束或工作流程变化时；本轮只补本手册维护规则 |
| [ROADMAP.md](../ROADMAP.md) | M1–M5 阶段、推荐顺序和里程碑出口 | 阶段或排序变化时；不维护第二套任务状态 |
| [CHANGELOG.md](../CHANGELOG.md) | 已交付改动与历史回填；Unreleased 不等于发布 | 实际交付后更新，不能把 planned 项写入完成记录 |
| [docs/IDEA_LOG.md](../docs/IDEA_LOG.md) | 用户原始想法、来源、观察、合并/暂缓决策和任务关联 | 新想法或新证据出现时追加历史，保留旧 ID |
| [docs/PRODUCT_BACKLOG.md](../docs/PRODUCT_BACKLOG.md) | 正式任务唯一状态入口；P0–P3、成本、风险、依赖、验收 | 任务创建、复评、实施或验收状态变化时 |
| [docs/VERIFICATION.md](../docs/VERIFICATION.md) | 分批次记录真实通过/失败/跳过/未执行及环境限制 | 执行了检查或验收后追加；保留历史，不把旧结果视为本轮重跑 |
| [docs/LEARNING_GUIDE.md](../docs/LEARNING_GUIDE.md) | Java 概念对照、LangGraph/Tool Calling/事务/错误与阅读练习 | 关键概念或学习示例因实现变化时 |
| [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) | 实体关系、图/工具、确定性规则、事务/恢复/部署边界 | 数据关系、事务或架构决策变化时；正文应再次对照源码 |
| [docs/IMPLEMENTATION_PLAN.md](../docs/IMPLEMENTATION_PLAN.md) | 首次 MVP 检查与开发顺序的历史记录 | 通常保留原貌；更正历史事实时标明，不继续加正式待办 |
| [evals/README.md](../evals/README.md) | 固定案例、Mock 与可选 live 评测的运行边界 | 评测命令、案例格式、评分或输出改变时 |
| [docs/PROJECT_GUIDE.md](../docs/PROJECT_GUIDE.md) | 当前逐文件职责、调用链、任务定位和命令导航 | 重要文件/符号/职责/数据流/启动变化时按第八节维护 |

不要用本手册替代 Backlog 的优先级/状态，也不要把 ARCHITECTURE 的概述当成精确端点规范。例如源码 begin_run 已拒绝失败请求的同键重放，查幂等细节应结合 main.py 和 test_acceptance.py。

## 三、逐文件代码与配置索引

检查代号：**B** 后端 pytest，**Q** Ruff，**F** 前端 format/lint/typecheck/Vitest/build，**M** 隔离数据库迁移与 schema 差异，**P** 隔离 PostgreSQL 集成，**E** 隔离浏览器闭环，**S** PowerShell 5.1/7 解析与适用启动检查，**D** Docker/Compose，**L** 经明确启用的真实模型评测/人工复核。具体命令和条件见第六节；表中是修改后的建议检查，不表示本轮执行过。

### 3.1 后端源码与迁移

| 文件 | 具体职责 | 重要类/函数/常量 | 交互模块 | 何时修改 | 修改后检查 |
| --- | --- | --- | --- | --- | --- |
| [backend/app/__init__.py](../backend/app/__init__.py) | 空的 Python 包标识文件；当前没有初始化逻辑 | 无自有类/函数 | 让 app.* 可作为包导入 | 确需包级初始化/导出时；避免隐式业务或数据库写入 | B、Q |
| [backend/app/config.py](../backend/app/config.py) | 从环境与 .env 读取数据库、模型、CORS；计算实际 Mock 模式 | Settings、Settings.effective_mock、settings | db.py、main.py、ModelAdapter、Alembic env.py；settings 用 lru_cache | 增改环境字段、默认值/校验或 Mock 选择；环境变化后重启进程 | B、Q；涉及 Live 再做 L |
| [backend/app/db.py](../backend/app/db.py) | 构造 Engine/Session；SQLite 连接启用外键；提供请求 Session | Base、make_engine、get_session；engine、SessionLocal | models 的基类、FastAPI Depends、测试 fixture；数据库不在这里自动建表 | 数据库连接策略、外键开关、Session 生命周期改变时 | B、Q、M、P |
| [backend/app/models.py](../backend/app/models.py) | 定义 六张表 的实体/关系和审计字段；JSON 用新对象赋值更新 | Timestamp、Star、Quest、QuestStar、Reflection、UserPreference、AgentRun；now、uid | Base；main/tools 查询与写入；迁移 metadata | 字段、约束、索引、实体关系、时间约定变化时必须配新迁移 | B、Q、M、P；接口变化加 F/E |
| [backend/app/schemas.py](../backend/app/schemas.py) | 运行时 DTO 与工具 JSON schema；拒绝多余字段、约束范围、验证 URL/标签 | StrictModel、StarInput、DraftResult、AgentRequest、Proposal、ProposalResult、Decision、ReflectionInput、Preferences；valid_url、clean_tags、valid_range；七个 Args 类见工具表 | FastAPI 请求、工具注册、模型输出；对应前端 types.ts | 字段/状态/工具参数、未知值或输入边界变化时；同步 types、表单与案例 | B、Q、F、E；输出影响评测时 L |
| [backend/app/retrieval.py](../backend/app/retrieval.py) | 中文二元词组/英文数字词匹配；取前 20 结果；用真实共同标签/非未分类类别构造关联；序列化补 UTC | tokens、search、relations、record_dict、star_dict | Star ORM；main 的检索/列表/关联；ToolRegistry 搜索 | 分词、排序、归档筛选、关联规则或时间序列化改变时 | B、Q；搜索/关联 UI 变更加 F/E；比较检索先标注评测 |
| [backend/app/semantic.py](../backend/app/semantic.py) | 只有 Embedding 和语义检索 Protocol；当前没有实现，也没有被工作流调用 | EmbeddingProvider.embed、SemanticRetriever.search | 未来独立检索器接口；现用 retrieval.search | RETR-001 有证据后实现具体检索器并定义更新/回退策略 | 实现后 B、Q 和同集关键词/语义评测；当前不声称语义检索已通过 |
| [backend/app/rules.py](../backend/app/rules.py) | 模型提示与后端约束验证共享同一份允许约束/文字步骤 | SUPPORTED_CONSTRAINTS、TEXT_STEPS | ModelAdapter.proposals、ToolRegistry.validate_quest_proposal、模板测试 | 增加可验证约束或体验模板时，不能只改模型 Prompt | B、Q；重点模板/约束测试，必要 L |
| [backend/app/model_adapter.py](../backend/app/model_adapter.py) | 统一 Mock/Live；Mock 固定主题/文字体验；Live 强制一个指定工具且拒绝额外坏调用、校验结构；百炼 Qwen 专用非思考参数与实际 usage；异常只暴露分类 | ModelFailure、ModelAdapter.request、ModelAdapter.draft、ModelAdapter.proposals、last_usage | Settings、schemas、rules、ChatOpenAI；ToolRegistry 读取其结果 | 提取/建议规则、SystemMessage Prompt、服务参数、错误分类改变时 | B、Q；重点 test_model_template/test_acceptance/非法输出；真实兼容性须 L |
| [backend/app/tools.py](../backend/app/tools.py) | 八个受控工具的参数校验/批准守卫/审计；读取、确定性验证、事务内写 Quest/Reflection 与候选偏好 | ToolRegistry.call；八个同名 handler 见工具表 | session、ModelAdapter、schemas、retrieval、rules、ORM；由 Workflow/main 编排 | 工具名/参数/权限、约束验证或写入规则改变时 | B、Q、P；重点工具拒绝、审批二次验证、反馈和幂等；闭环 E |
| [backend/app/workflow.py](../backend/app/workflow.py) | 真实 StateGraph 分支与短图；节点包装持久化快照/事件；生成图不写正式实体 | AgentState、Workflow.node/execute/retrieve/generate/validate/approved_operation；finish_run | ToolRegistry、AgentRun、AgentRequest；main 调用与提交事务 | 节点/边/公开 state/失败记录/恢复语义变化时 | B、Q；重点 test_langgraph_steps_tools_and_approval、失败/重试；E，必要 L |
| [backend/app/main.py](../backend/app/main.py) | FastAPI 入口；路由、用例编排、审批事务、请求幂等和 HTTP 错误；没有另设 service.py | app；begin_run、execute_run、decide（内部 persist_star）、reflect、retry_run；其余端点见路由表 | Depends(get_session)、schemas、ORM、Workflow、adapter、retrieval；前端 api | API、返回结构、幂等、用户批准、反馈、偏好或实体 CRUD 改变时 | B、Q、P；重点 test_mvp/test_acceptance；接口变化 F/E |
| [backend/migrations/env.py](../backend/migrations/env.py) | Alembic offline/online 运行入口；读取 Settings URL，导入 ORM 注册 metadata，online 比较类型 | config、target_metadata；context.configure/run_migrations | alembic.ini、Base.metadata、models、Settings、数据库 | 迁移连接、metadata 注册、schema/type 比较改变时 | M、P；不要对个人库回滚 |
| [backend/migrations/script.py.mako](../backend/migrations/script.py.mako) | 新 revision 的 Mako 模板，填入 revision 元信息和 upgrade/downgrade | 模板占位 message/up_revision/down_revision/upgrades/downgrades | alembic revision 命令 | 确需修改新迁移的生成格式时 | 隔离库生成并审查新迁移，再 M/P；本轮未执行生成命令 |
| [backend/migrations/versions/0001_initial.py](../backend/migrations/versions/0001_initial.py) | 初始建 六张表；Quest 候选唯一键、Reflection 唯一 quest_id、关联外键；反序删表 | revision=0001、timestamps、upgrade、downgrade | models 元数据；env.py 调用 | 已使用的初始迁移保留；今后结构变更新增 revision，不直接改它充当升级 | M、P；downgrade 只在一次性隔离库 |

### 3.2 前端源码与配置

| 文件 | 具体职责 | 重要入口/符号 | 交互模块 | 何时修改 | 修改后检查 |
| --- | --- | --- | --- | --- | --- |
| [frontend/index.html](../frontend/index.html) | 中文页面、viewport/theme 元信息、#root 与 /src/main.tsx 入口 | root DOM、module script | Vite → main.tsx；Nginx 提供构建结果 | 页面元信息、挂载点或静态入口改变 | F、E；容器 D |
| [frontend/src/main.tsx](../frontend/src/main.tsx) | 挂载 App，加载全局 CSS，启用 React.StrictMode | ReactDOM.createRoot、App | index.html root、App.tsx、styles.css | 挂载/全局 provider 或启动样式改变 | F、E |
| [frontend/src/App.tsx](../frontend/src/App.tsx) | 八个页面、服务器数据刷新、草稿/候选审批、错误/运行恢复、星星与反馈弹窗；页面未拆成独立文件 | App；refresh、act、openRun、generate、decision；UsageGuide、SavedStarNextStep、PageTitle、ResultHeading、Modal；pages、blankStar、initialPreferences | api、types、components、全部相应 /api 端点；页面明细见下表 | 输入提示、引导、页面交互/状态、反馈和可见审计改变；UX-001/002/003 的主要位置 | F；重点 App.test、组件测试；完整行为 E，审批变化 B |
| [frontend/src/components.tsx](../frontend/src/components.tsx) | 通用编辑/展示；StarDetails 负责只读真实字段、安全文本/来源和未知值；StarEditor 保留原表单；列表解析与体验提交不变 | split、numeric、energyNames、statusNames、ListInput、OrbitArt、Empty、StarCard、StarDetails、StarEditor、ProposalEditor、ProposalFacts | App、types；ListInput 有独立 raw 字符串，StarDetails 不写 API | 字段展示、查看/编辑语义、安全链接、表单/锁定和数值改变 | F；重点 components.test/App.results；真实双尺寸/读写边界 E |
| [frontend/src/api.ts](../frontend/src/api.ts) | fetch('/api' + path)，JSON 请求及可选 Idempotency-Key；204 转 undefined；错误保留可用 run_id | ApiError、api<T> | App、Vite/Nginx 代理、FastAPI detail；泛型只做类型声明，无运行时 JSON schema 校验 | 请求头/错误格式、返回约定、代理路径改变 | F；重点 api.test；真实链路 E |
| [frontend/src/types.ts](../frontend/src/types.ts) | 前端接口形状和状态，和后端 Pydantic/实际 JSON 共同构成契约 | Energy、StarInput、Star、Proposal、Reflection、Quest、Match、AgentRequest、Run、Preference、PreferenceData、Stats、Relation | App/components/api 的类型参数；非自动生成 | 后端入参/返回字段、枚举或前端需要显示字段改变；Run.state 是前端用到的部分，不等于全部数据库 state | F；接口/状态变化 B/E |
| [frontend/src/styles.css](../frontend/src/styles.css) | 原生 CSS 的配色、卡片、轨迹、CSS 陪伴、焦点、弹窗和响应式；末尾还有可读性覆盖规则 |  :root 变量；.companion、.orbit-art、.star-grid、.runs-layout、.modal；600/850/1150/1450px 媒体查询 | App/components className、OrbitArt 内联 SVG 色值；无 Tailwind 配置 | UI-001/002 视觉、布局、字体/对比度或移动导航改变 | F、E；桌面/移动截图和人工视觉/键盘复核；单测不能证明审美或对比度 |
| [frontend/src/test-setup.ts](../frontend/src/test-setup.ts) | 导入 jest-dom 断言，补 JSDOM 缺失的 scrollIntoView mock；真实几何由浏览器验证 | @testing-library/jest-dom/vitest、vi.fn | vite.config.ts 的 setupFiles、组件测试 | 测试初始化与断言环境改变 | F（至少 Vitest + 类型/lint） |
| [frontend/src/App.results.test.tsx](../frontend/src/App.results.test.tsx) | UX-002 一次性定位、页面/Modal 焦点边界、真实 ID 导航、过期/失败/重试/恢复 | 状态化 server fixture、scrollIntoView 调用、真实 API 方法/次数断言 | App、api、types、test-setup、Testing Library；无真实网络 | 结果衔接或恢复状态改变 | F；几何/实际 DB 计数另用 E |
| [frontend/e2e/results.mjs](../frontend/e2e/results.mjs) | 被 smoke 调用的双尺寸结果定位/Tab/减少动画、刷新恢复、精确 Star/Quest 与无重复写检查 | verifyResults；E2E_INJECTED_FAILURE 可选隔离故障 fixture | Playwright page、已核验的隔离后端；不自行启动服务 | ID、结果区域、导航/错误/恢复改变 | F lint/format + E；无故障 fixture 时明确 skip，不能宣称真实 retry 已测 |
| [frontend/src/App.test.tsx](../frontend/src/App.test.tsx) | 模拟 api，检查空档案/Mock、审批边界、连接失败；UX-003 单草稿/链接提示、5 元偏好下空/0/8 元请求、偏好空值和范围 | backend(mock, maxBudget) 辅助函数；含参数化用例；vi.mock api | App、api、Testing Library；不是服务集成测试 | 页面状态或交互边界改变 | F；增加覆盖需要的状态而不是宣称新引导已测 |
| [frontend/src/components.test.tsx](../frontend/src/components.test.tsx) | 检查未知值/来源锁、ListInput 分隔、ProposalEditor 方案字段与多行输入、空值/0 元、输入说明和 Schema 范围 | 固定 star/proposal fixture；清空再保存与可访问说明断言 | ListInput、StarEditor、ProposalEditor、ProposalFacts | 编辑器、拆分规则或金额展示改变 | F；真实提交规则仍由 B/E 验证 |
| [frontend/src/api.test.ts](../frontend/src/api.test.ts) | 检查批准请求体/幂等头与失败 ApiError 的 runId | 两个 it；vi.stubGlobal(fetch) | api、ApiError；模拟 Response | 请求/错误处理改变 | F；不是在线服务成功证据 |
| [frontend/e2e/smoke.mjs](../frontend/e2e/smoke.mjs) | Playwright 真浏览器闭环；检查 5 元偏好下空/0 元请求、页面异常，收集/探索/偏好在 1440/390px 的溢出并截图 | chromium.launch；E2E_ALLOW_WRITE、E2E_BASE_URL、E2E_ARTIFACT_DIR | 运行中的前端/后端；输出 .cache/e2e；TEMP/TMP 指向 artifact/browser-tmp | 交互文案、选择器、流程/截图输出改变；文案改动要查这里精确 label | F lint + E；只用隔离库，授权开关不自动核验数据库地址 |
| [frontend/vite.config.ts](../frontend/vite.config.ts) | React 插件；开发 /api 代理到 127.0.0.1:8000；Vitest jsdom/setupFiles | defineConfig；server.proxy、test | 开发服务器、FastAPI、test-setup.ts | 后端端口、开发代理、测试环境改变 | F、E；代理变更实际启动核对 |
| [frontend/tsconfig.json](../frontend/tsconfig.json) | ES2022、strict、Bundler 模块解析、react-jsx、noEmit；检查 src 与 vite.config.ts | compilerOptions、include | tsc --noEmit / tsc -b、IDE | 编译目标、类型边界或包含目录改变 | F 的 typecheck/build；不把编译通过当运行时通过 |
| [frontend/eslint.config.js](../frontend/eslint.config.js) | ESLint flat config：TS/React Hooks、Node JS、E2E 同时允许浏览器/Node globals；忽略 dist 等 | tseslint.config；hooks.configs.recommended.rules | 所有前端自有 JS/TS；npm run lint | lint 规则、文件环境/忽略改变 | F lint/typecheck，确认 E2E 脚本被检查 |
| [frontend/package.json](../frontend/package.json) | Node >=22.13.0、React/Vite 等依赖范围与 dev/build/typecheck/lint/test/test:e2e/format 脚本 | scripts；build=tsc -b && vite build | npm、lock、Vite、CI、Dockerfile | 必要依赖或 npm 脚本改变；本轮不修改 | F；锁安装检查；容器/CI/文档联动 |
| [frontend/package-lock.json](../frontend/package-lock.json) | npm 解析的精确依赖树与根包信息；当前 lockfileVersion=2 | packages、根 engines | npm ci、package.json、Node、CI/Docker 构建 | 确有依赖变更时由 npm 生成，不手改版本猜兼容性 | npm ci 后 F，记录实际环境；本轮只静态读取锁元数据 |
| [frontend/.dockerignore](../frontend/.dockerignore) | 只排除该 frontend 构建上下文中的 node_modules/dist/log | 忽略规则；与根 .gitignore、.dockerignore 不同 | frontend Dockerfile 的 COPY . . | 前端构建上下文或产物改变 | D；实际审查上下文是否包括私有文件，不能假定 Git 忽略等于 Docker 忽略 |
| [frontend/Dockerfile](../frontend/Dockerfile) | Node 22-alpine npm ci/build → nginx:alpine 静态产物 | 两个 FROM 阶段、COPY --from=build | package/lock、全部前端源码、nginx.conf、Compose | 镜像/打包/资源路径改变 | F、D；本机历史构建不证明镜像已构建 |
| [frontend/nginx.conf](../frontend/nginx.conf) | 容器 /api/ 转发 backend:8000，180 秒读取超时；其他 URL 回落 index.html | location /api/；proxy_pass；try_files | Compose backend 服务名和构建后的静态资源 | 生产代理、超时或静态页面路由改变 | D、E（目标容器）；与 Vite 开发代理分开验证 |

八个页面都位于 App.tsx 的条件渲染分支，pages 配置与 Page 联合类型控制导航；没有 React Router 或独立 pages/ 目录。

| page 值 | 页面 | 实际数据/调用 |
| --- | --- | --- |
| home | 我的星屿 | 最近 Star、真实统计、收集/探索入口；refresh 的 /stars 和 /stats |
| collect | 收集星星 | 原始文字/来源输入；generate(collect)；StarEditor/sourceLocked 的草稿审批；手动表单直接 POST /stars |
| archive | 星星档案 | /stars?q= 搜索得到 searchIds；本地类别/状态筛选；StarCard 默认只读详情，明确选择后进入编辑 |
| relations | 兴趣轨道 | /relations 真实边与理由；点击关联 Star 打开档案编辑 |
| explore | 微型探索 | 时间/预算/精力；generate(explore)；依据/不确定性；decision 接受/放下、ProposalEditor 修改候选 |
| quests | 体验手记 | /quests；accepted 体验可 PUT 修改和 POST reflections；completed/skipped 展示真实反馈 |
| runs | Agent 足迹 | /agent/runs 最新 50 条；selectedRun 事件/状态；失败生成 retry；待确认结果回 collect/explore |
| preferences | 我的偏好 | 明确偏好 PUT/DELETE；候选按 reflection_id 查看、POST confirm 或 DELETE |

refresh 并行拉取七类数据；act 管理 busy/错误/提示，成功后 refresh，带 runId 的 ApiError 可打开失败足迹。generate 给一次生成请求新建随机幂等键；decision 再查询运行更新草稿/候选。它们是 App 内函数，不是独立服务模块。

### 3.3 测试、评测与 CI

| 文件 | 具体职责 | 重要入口/符号 | 交互模块 | 何时修改 | 修改后检查 |
| --- | --- | --- | --- | --- | --- |
| [backend/tests/conftest.py](../backend/tests/conftest.py) | 导入前强制 Mock、空 Key、禁用 .env/tracing 和 .cache/test-import.db；每测试 tmp_path/test.db 建表；覆盖 get_session | db、client、star、proposal_run、quest；override | FastAPI TestClient、make_engine、Base.metadata.create_all；测试直接建表不验证迁移 | fixture、隔离、初始记录或测试请求改变 | B、Q；确认仍不连接个人库/真实模型 |
| [backend/tests/test_mvp.py](../backend/tests/test_mvp.py) | API/图/工具/数据库边界；含固定 Mock 提取案例；模拟 Live 非法结构/工具 | test_draft_confirmation_no_automatic_write、test_langgraph_steps_tools_and_approval、test_edited_proposal_validates_again、test_model_failure_audited_and_retry、test_reflection_persisted_candidates_need_confirmation 等 | client/db fixture、所有核心后端模块、evals/cases.json extraction | 业务规则、约束、审批、反馈、检索或恢复改变 | B、Q；参数化测试数量不等于函数个数；不声称是真模型评测 |
| [backend/tests/test_acceptance.py](../backend/tests/test_acceptance.py) | 验收回归：失败生成/反馈同键重放不报成功；模拟超时/限流/连接异常的脱敏分类 | test_failed_generation_key_does_not_return_created、test_failed_reflection_key_does_not_claim_saved、test_provider_failure_classification_is_sanitized | begin_run、ModelAdapter、AgentRun/Star/Reflection | 幂等状态或错误分类改变；保持失败审计和记录计数断言 | B、Q；这些服务异常由 FakeModel 模拟 |
| [backend/tests/test_model_template.py](../backend/tests/test_model_template.py) | 在模拟 request 下检查真实模式 payload 传精确允许步骤与 0 预算 | test_live_model_receives_exact_supported_constraint_template | ModelAdapter.proposals、TEXT_STEPS、Preferences | 受支持约束或模型 payload 改变 | B、Q；名字包含 live，但此测试不调用真实模型 |
| [backend/tests/test_qwen_adapter.py](../backend/tests/test_qwen_adapter.py) | 真实 LangChain/SDK + httpx2 内存传输捕获实际 JSON，错误工具/结构/usage/来源及隔离库审批回归 | wire、forbid_network、test_qwen_wire_payload_and_unknowns | ChatOpenAI、MockTransport、ModelAdapter；不记录 headers；仅允许事件循环 loopback 自唤醒 | 锁版本、序列化、专用参数、解析/错误分类改变 | B/Q 离线，不代表 L 真实服务 |
| [backend/tests/test_live_runner.py](../backend/tests/test_live_runner.py) | Fake 配置/模型的授权、数量、北京 URL/Key/非 Mock 预检与停跑/脱敏报告测试 | config、test_preflight_rejects_before_adapter、test_main_bounded_public_cases_and_failure_stop | importlib 加载 runner；tmp_path 报告；禁止网络；不读取私有 .env | runner 预检、CLI、报告/计数改变 | B/Q 离线；main 参数包含授权字符串也只调用 Fake |
| [backend/tests/test_postgres.py](../backend/tests/test_postgres.py) | 只有 TEST_POSTGRES_URL 存在才运行；独立随机 schema 验证 JSON 与外键保护，finally 清理 | test_postgres_json_and_foreign_key | make_engine、Base、Star/Quest/QuestStar；直接 create_all，不是迁移回滚测试 | 目标数据库约束/类型改变 | P、Q；需要能创建/删除专用 schema 的隔离数据库 |
| [evals/cases.json](../evals/cases.json) | 三个 extraction 固定输入及 Mock 期望标签；另有七个 scenarios 的预期行为说明 | extraction、scenarios；ocean-space/unknown/explicit-source | test_fixed_extraction_eval_cases 读取 extraction；run_live.py 只遍历 extraction | 案例/期望或人工基线改变 | B + JSON 格式；L 只验证实际覆盖项；scenarios 不是自动数据驱动全套测试 |
| [evals/run_live.py](../evals/run_live.py) | 显式 --allow-live、非 Mock/Key/模型/URL/零重试预检；默认 --max-cases 1；失败停止；公开结构/耗时/实际 usage 输出 .cache/live-eval.json | main、positive_count、validate_live_config、run_cases；executed_cases、results | Settings、ModelAdapter.draft、AgentRequest、公开 cases.json；不导入 db/workflow | 预检、CLI、请求范围/报告改变 | Q 离线；L 本阶段禁止，不是完整 EVAL/审批验证 |
| [.github/workflows/ci.yml](../.github/workflows/ci.yml) | push/PR 两 job；Ubuntu + PostgreSQL 16 + Python 3.12/uv；Node 22 前端 | backend/front-end job 名实际为 backend、frontend；MVP checks | 根 uv/迁移/Ruff/pytest；前端 npm ci 与格式/lint/type/test/build；专门 PG 测试 step | 检查集合、环境版本/依赖缓存或触发条件改变 | 本地 B/Q/F/M/P，最终核对真实 CI run；目前未含 Docker 构建、浏览器 E2E 或 Live eval |

普通 pytest 使用 conftest 的 Mock/隔离 SQLite，Base.metadata.create_all 是测试准备，不证明 Alembic 迁移正确。CI 先做 PostgreSQL Alembic/Ruff，再 mkdir -p .cache，之后普通 pytest（PostgreSQL 用例因无 TEST_POSTGRES_URL 跳过），最后单独带 TEST_POSTGRES_URL 执行 PostgreSQL 用例。首次远程运行在普通 pytest 失败，最后一步未执行；2026-10-17 已补记 [修复后的成功运行](https://github.com/YOLIIIIII/wonder-orbit/actions/runs/39030090153)，两个 Job 成功，独立 PG 实际 1 passed，原失败记录保留。检查哪些 job 真运行过要看远程结果；YAML 不能代替执行证据。

### 3.4 根配置、后端容器与启动脚本

| 文件 | 具体职责 | 重要入口/符号 | 交互模块 | 何时修改 | 修改后检查 |
| --- | --- | --- | --- | --- | --- |
| [pyproject.toml](../pyproject.toml) | Python >=3.12,<3.14 依赖范围/dev 组；pytest testpaths/pythonpath/.cache basetemp；Ruff py312 和规则 | project、dependency-groups、tool.pytest.ini_options、tool.ruff | uv.lock、uv、pytest/Ruff、CI；不是另一个 requirements.txt | 依赖/运行版本或测试/格式规则变更 | B、Q；uv lock --check --offline，必要 F/M/D |
| [uv.lock](../uv.lock) | 精确 Python 解析记录；当前 69 个 package、lock version=1 | requires-python、package | uv sync --frozen、pyproject、CI/backend 镜像 | 确有依赖调整时由 uv 生成，不手工改包内部 | 锁校验、frozen 安装、B/Q；本轮只解析 TOML 和元数据 |
| [alembic.ini](../alembic.ini) | 迁移位置与 backend 导入路径 | script_location=backend/migrations；prepend_sys_path=backend | alembic、migrations/env.py | 迁移目录/包路径改变 | M、P；uvicorn 仍需要自身 PYTHONPATH |
| [.env.example](../.env.example) | 可提交占位数据库/Mock/模型/CORS 配置；API Key 为空 | DATABASE_URL、MOCK_MODE、MODEL_API_*、MODEL_NAME/TIMEOUT/MAX_RETRIES/MAX_TOKENS、CORS_ORIGINS | Settings、用户私有 .env、Compose env_file | 环境字段/默认值或说明改变 | 核对 Settings 与启动条件；B，必要 D/L；不要填真实凭据 |
| [.gitignore](../.gitignore) | 排除环境变体、DB及附属文件、venv/tools/cache、依赖/产物/日志，保留 .env.example | 忽略/反忽略规则 | Git 候选文件；测试/运行产物 | 新增运行产物路径或配置命名改变 | git check-ignore -- 路径 与 git status/ls-files；不能以规则存在证明已暂存的文件被移除 |
| [.dockerignore](../.dockerignore) | 根 Docker 构建上下文的排除规则；不是 Git 规则的复制 | 排除 .git/.env/.venv/.tools/.cache、依赖/产物/pycache、*.db | Compose backend context=根目录、backend Dockerfile | 镜像上下文/敏感文件范围变化 | D 与上下文审查；当前规则不等于 .env.* 和所有 SQLite 变体均已排除 |
| [docker-compose.yml](../docker-compose.yml) | PostgreSQL 16 + 后端 + 前端；回环端口 5432/8000/8080；named volume wonder_data；等 DB 健康 | services db/backend/frontend；db healthcheck；backend DATABASE_URL 指向 db | 两个 Dockerfile、.env、Nginx backend 主机名 | 服务连接/镜像/端口/卷/健康依赖改变 | D、M/P、E；开发 wonder 用户/密码为占位 |
| [backend/Dockerfile](../backend/Dockerfile) | Python 3.12-slim + uv 0.13.0，frozen 无 dev 安装；启动先迁移后 uvicorn | PYTHONPATH=/app/backend；CMD sh -c 的两个 uv run --no-sync | 根上下文、pyproject/uv.lock、alembic、backend | Python/uv 镜像、安装或后端启动改变 | D、M/P、B/Q；容器 0.0.0.0 由 Compose 本机端口绑定隔离 |
| [scripts/dev.ps1](../scripts/dev.ps1) | 回到项目根；优先项目 uv/Node，设项目缓存/PYTHONPATH；可选 SQLite；sync → migrate → uvicorn | param([switch]$Sqlite)；$uvPath；$env:DATABASE_URL；LASTEXITCODE 检查 | uv.lock、alembic、app.main；-Sqlite 指向真实 wonder.db | Windows 后端启动、工具路径或数据库切换改变 | S、B/Q、M；启动会装依赖/迁移，不是只读语法检查 |
| [scripts/web.ps1](../scripts/web.ps1) | 优先项目 Node，切 frontend；检查 Vite 依赖，直跑 Vite，默认端口 5173 | param([int]$Port=5173)；node_modules/vite/bin/vite.js 守卫 | frontend 依赖、vite.config.ts、用户端口 | Node 路径、依赖守卫或前端启动改变 | S、F；启动后 HTTP/代理检查；UTF-8 BOM，dev.ps1 全 ASCII |

Git 忽略和 Docker 上下文排除是两套机制，现有规则不完全相同。本轮没有构建/查看镜像内容，不把“Git 已忽略”解释为“不会进入 Docker 构建上下文”；新建私有配置或产物时分别核对。

六张实际表为 stars、quests、quest_stars、reflections、user_preferences、agent_runs。Quest.based_on_star_ids 是 API 从 QuestStar 关系查出的列表，**不是 Quest 表中的一个 JSON 字段**；候选 proposal 保存在 AgentRun.state，正式 Quest 从 accepted 开始。Reflection.quest_id 唯一；UserPreference 使用 id=1 的单用户记录，explicit 与 candidates 分开，不存在账号/User 实体。

运行 .env、wonder.db、.cache/pytest、.cache/e2e、.cache/live-eval.json、.venv、.tools、frontend/node_modules、frontend/dist 均是私有/运行/依赖产物，不属于自有代码索引。目录可能因环境而存在或不存在；正式表通过 Alembic 初始化，不靠全局 Python 列表或前端 state 保存。

### 3.5 当前全部 API 路由

以下 HTTP 路径和处理函数来自 main.py 的 app 装饰器。FastAPI 自动文档位于 /docs，不是业务聊天路由。

| 方法 | 路径 | main.py 处理函数 |
| --- | --- | --- |
| GET | `/api/health` | `health` |
| GET | `/api/stats` | `stats` |
| GET | `/api/stars` | `list_stars` |
| GET | `/api/stars/{star_id}` | `get_star` |
| POST | `/api/stars` | `create_star` |
| PUT | `/api/stars/{star_id}` | `update_star` |
| DELETE | `/api/stars/{star_id}` | `delete_star` |
| GET | `/api/search` | `search_stars` |
| GET | `/api/relations` | `get_relations` |
| POST | `/api/agent/runs` | `create_run` |
| GET | `/api/agent/runs` | `list_runs` |
| GET | `/api/agent/runs/{run_id}` | `get_run` |
| POST | `/api/agent/runs/{run_id}/retry` | `retry_run` |
| POST | `/api/agent/runs/{run_id}/decision` | `decide` |
| GET | `/api/quests` | `quests` |
| PUT | `/api/quests/{quest_id}` | `edit_quest` |
| POST | `/api/quests/{quest_id}/reflections` | `reflect` |
| GET | `/api/preferences` | `preferences` |
| PUT | `/api/preferences` | `put_preferences` |
| DELETE | `/api/preferences` | `clear_preferences` |
| POST | `/api/preferences/candidates/{candidate_id}/confirm` | `confirm_preference` |
| DELETE | `/api/preferences/candidates/{candidate_id}` | `remove_candidate` |

## 四、一次请求如何执行

### 4.1 入口与公开状态

浏览器加载 index.html → main.tsx → App。App.refresh 获取实际档案和模式；用户提交时 App.act 调 App.generate → api<Run>，带新 Idempotency-Key 发 POST /api/agent/runs。Vite 或 Nginx 代理到 main.create_run；FastAPI 用 AgentRequest 校验，用 get_session 提供 Session。

create_run → begin_run：请求类型和 payload 摘要绑定请求键，先提交 AgentRun(running)。同键不同请求、运行中或此前 failed 返回 409；已成功/待确认等已保存结果可返回原运行。execute_run → Workflow(session, adapter(), run).execute(request)。adapter 构造 ModelAdapter(settings())。

AgentState 的公开字段是 request、related_stars、star_details、preferences、draft、proposals、questions、validation、result；node 包装器把公开 state 与工具/节点事件写入 AgentRun。它不保存隐藏推理，也不是普通聊天记录。

```mermaid
flowchart TD
    U["App.generate → api POST /api/agent/runs"] --> A["main.create_run → begin_run → execute_run"]
    A --> N["Workflow.execute: understand_request"]
    N --> K{request_type}
    K -->|collect| C["extract_star_draft"]
    K -->|explore| R["retrieve_related_stars"]
    R --> P["load_preferences"]
    P --> G["generate_suggestions"]
    G --> V["validate_suggestions"]
    C --> W["await_user_decision → END"]
    V --> W
    W --> O["HTTP 返回已持久化结果 awaiting_decision"]
    O --> H["用户预览/编辑/确认或放下"]
    H --> D["新 HTTP 请求 → main.decide"]
    D --> B{approved}
    B -->|false| X["只保存决定，不建正式记录"]
    B -->|true| T["重验后 approved_operation: persist_approved_result"]
    T --> Q["Star 或 Quest/QuestStar 与审批一起提交"]
    Q --> F["用户实际反馈 → main.reflect → process_reflection"]
```

这是两次（反馈则更多次）独立 HTTP 请求，不是一个常驻图挂在那里等用户；await_user_decision 只经过空更新节点后返回。当前没有 interrupt/checkpointer。understand_request 也是明确 DTO 校验/分支，不是让模型自主决定写数据库。

### 4.2 生成节点与具体调用

| 节点 | workflow.py 的实现 | 工具/下游调用 | 结果 |
| --- | --- | --- | --- |
| understand_request | execute 内 node 包装的 lambda | AgentRequest.model_validate | request 契约与 collect/explore 分支 |
| extract_star_draft | execute 内 lambda | tools.call(create_star_draft) → ModelAdapter.draft | draft（包含 draft/missing_fields/questions）；当前一次一张 |
| retrieve_related_stars | Workflow.retrieve | search_stars；前 3 条 get_star_details | related_stars（最多 20）、star_details |
| load_preferences | execute 内 lambda | get_user_preferences | 明确 preferences，候选推测不直接参与 |
| generate_suggestions | Workflow.generate | 按明确类别与检索 score 排序 → generate_quest_proposal → ModelAdapter.proposals | proposals/questions；Mock 最多 3 个免费文字体验 |
| validate_suggestions | Workflow.validate | 每个候选 validate_quest_proposal | 只留下通过候选，保存 validation；无法满足则返回问题 |
| await_user_decision | execute 内空 lambda | 无模型或正式写工具 | END 后 run.status=awaiting_decision，摘要与 finish_run 落库 |

注意两个真实细节：get_star_details 虽填充 star_details，当前 generate 用的是排序后的 related_stars，并未将全量详情自动放入模型提示；/api/stars?q= 按命中 ID 筛选后又按 created_at 排序，不等于 search 的相关性顺序。直接搜索 API 可查归档，而生成图工具默认不推荐归档。

ModelAdapter.draft 在 Mock 下用固定 topic_map 命中标签、保留未知原因/预算/精力；Live 调 request(create_star_draft, DraftResult, payload)。ModelAdapter.proposals 先合并时间/预算/精力的较严格上限，对不支持约束、无历史或时间冲突返回 questions；可以生成时才走 Mock 模板或 request(generate_quest_proposal, ProposalResult, payload)。

ModelAdapter.request 创建 ChatOpenAI，绑定且强制一个工具名，要求恰好一个 tool_call，再用 schema.model_validate 解析参数。注册层的 create_star_draft 入参是 AgentRequest，模型被要求提交的结果 schema 是 DraftResult；generate_quest_proposal 注册入参 ProposalArgs，模型返回 schema 是 ProposalResult。两种 schema 的职责不同，不能把模型返回参数直接当成数据库工具执行许可。

### 4.3 八个工具与权限

| 工具名 | ToolRegistry 参数类型（schemas.py） | handler 的实际动作 | requires_approval |
| --- | --- | --- | --- |
| search_stars | SearchArgs | retrieval.search；默认排除归档兴趣，返回真实 ID/text/score/match_basis | 否 |
| get_star_details | DetailArgs | session.get(Star) 与 star_dict；不存在返回 404 | 否 |
| get_user_preferences | EmptyArgs | 读取 UserPreference(id=1).explicit，校验为 Preferences | 否 |
| create_star_draft | AgentRequest | ModelAdapter.draft → DraftResult 校验；仅产草稿结构 | 否 |
| generate_quest_proposal | ProposalArgs | ModelAdapter.proposals(request, stars, preferences) | 否 |
| validate_quest_proposal | ValidateArgs | 引用子集/存在性、时间、预算、精力、支持约束的确定性规则 | 否 |
| persist_approved_quest | PersistArgs | 唯一 proposal_key 防重；创建 Quest 和 QuestStar；工具内再检查 ID 存在 | 是 |
| record_reflection | ReflectionArgs | accepted Quest 才可写；保存 Reflection/结果并由明确喜欢产生未确认候选 | 是 |

ToolRegistry.call 顺序是名字允许列表 → Pydantic 参数 → 后端 approved 上下文 → handler → finally 记录工具状态/耗时。模型不能通过参数设置 approved；当前模型只通过指定工具提交结构结果，检索/验证/写入路径由后端图与 API 决定，不存在任意代码、SQL 或 shell 工具。

### 4.4 批准、正式写入与返回

App.decision 发 POST /api/agent/runs/{run_id}/decision，Decision 允许 approved、index 及可选 edited_star/edited_proposal。main.decide 用 with_for_update 查询 AgentRun，检查运行状态/候选索引及决定 fingerprint；相同决定重发返回已有结果，不同决定 409。

- collect 批准：decide 恢复请求原文/来源 → 内部 persist_star → Workflow.approved_operation(persist_approved_result) → Star flush；然后保存 decisions 并一次 commit。这里没有名为 persist_approved_star 的注册工具。
- explore 批准：重新取明确偏好 → validate_quest_proposal 校验编辑后的候选及当前真实 ID → approved_operation 中调用 persist_approved_quest → Quest(accepted)/QuestStar flush → 同事务提交决定。验证失败保留验证事件且不创建 Quest。
- 放下：只写决定；不创建 Star/Quest。Quest 候选的 proposed 阶段在 AgentRun 内，数据库不是先插一行 proposed Quest 再改 accepted。
- App 随后 GET 原 run 并 refresh 所有数据。手动填写 StarEditor 的 POST /api/stars 是另一条用户直接保存路径，不运行提取图；编辑档案 PUT /api/stars/{id} 可以改表单原文，不能把审批阶段 sourceLocked 说成原文永久不可修改。

PostgreSQL 行锁、Quest.proposal_key 唯一与 Reflection.quest_id 唯一参与保护；现有测试证明顺序重发与冲突，不证明任意并发可靠。SQLite 的 with_for_update 没有同等锁语义。

### 4.5 反馈、偏好与失败恢复

体验弹窗 → api POST /api/quests/{quest_id}/reflections（新幂等键） → main.reflect/begin_run → approved_operation(process_reflection) → record_reflection。保存用户真实输入，将 Quest 改为 completed/skipped；liked_aspects 只形成附真实 reflection_id 的 candidates。main.confirm_preference 在用户明确确认后加入 explicit.categories 并移除候选；模型没有自动把反馈归纳成长期事实。每个 Quest 当前只有一次最终反馈，无反馈修改 API。

生成失败：execute_run rollback 后重新读取 run，保存 failed/error_type/summary、finish_run，返回 502 和 run_id；ModelFailure 只公开 timeout/rate_limit/model_unavailable/invalid_tool_call/invalid_model_output 分类。节点/工具事件和已提交快照用于审计；反馈失败的 reflect 特别恢复 failed_events，避免 rollback 丢事件。

带 run_id 的 ApiError 可使 App.act 打开失败运行；不带 run_id 的错误只显示错误。main.retry_run 仅 collect/explore 的 failed/running 可用，running 要等 max(120 秒, 4×MODEL_TIMEOUT) 保护期，新建运行重做读取/生成，不重放批准写入。UI 目前只为失败生成展示重试，运行页可打开待确认结果；列表最多取最近 50 条，已知 run_id 可调用详情 API。

UX-003 核对补充（2026-10-17）：App 的收集示例为单兴趣，草稿/链接说明可见；StarEditor/ProposalEditor 保留未知预算 null 和零预算差别。时间与预算 HTML 范围对齐 Schema，本次可用时间现可留空；精力显示低/中/高。ListInput 仍为单行 input，split 支持中英文逗号及换行，提示建议单行用逗号，未新增多行解析。共享说明用 useId 关联，避免同时出现多个编辑器时 ID 重复。smoke.mjs 已同步新 label，检查 5 元偏好下空预算/0 元及三个表单页面 1440/390px；执行前仍须自行核对隔离数据库。

## 五、常见开发任务定位

| 想改什么 | 首先看哪里 | 必须联动核对 | 验证与文档 |
| --- | --- | --- | --- |
| 输入示例/提示、预算空值（UX-003） | App.tsx collect/explore/preferences；components.tsx StarEditor/ProposalEditor/ListInput | schemas.py 字段范围与未知值；tools.validate_quest_proposal；E2E 的精确 label；预算留空仍受明确偏好上限约束 | F、B 中约束用例、E；更新相关 IDEA/Backlog 与真实 VERIFICATION/CHANGELOG，不宣称多草稿/抓取 |
| 首次引导与结果衔接（UX-001/002） | App.tsx home/collect/explore/quests/runs 与 generate/decision/act；Empty/Modal | 真实星星数量、待审批/已决定、失败/反馈状态；不得为导览插虚假记录 | F/E、审批 B；更新任务与验证；职责/导航变化再改本手册 |
| 视觉或陪伴（UI-001/002） | styles.css、components.OrbitArt、App 的 .companion | 末尾覆盖规则/媒体查询、提示/依据/Mock 可读性；已有占位可换但不改模型 | F/E、实际尺寸截图、人工检查；素材和待办状态同步 |
| 兴趣提取 | ModelAdapter.draft/request、schemas.StarInput/DraftResult、Workflow.execute collect 分支 | ToolRegistry.create_star_draft；App 草稿编辑/来源锁；cases.json；持久化 schema 改变需 ORM/迁移 | B/Q、明确的 L 与人工核对；EVAL/任务/验证，不能用 Mock 替代 Live |
| 工具参数/审批 | schemas 中 Args/Decision；ToolRegistry.call/handler；main.decide/begin_run | approved 只能由后端传；原始来源/当前偏好/真实 ID/幂等；Workflow.approved_operation 的 commit 边界 | B/Q/P；test_mvp、test_acceptance、E；架构/学习/本手册调用链 |
| DB 字段/关系 | models.py、db.py；Alembic env.py 与新增 versions revision | 新 DTO、types.ts、序列化、QuestStar FK、JSON 更新方式、测试 fixture；不要只运行 create_all | 隔离库 M/P、B/Q；API 变化 F/E；架构/本手册/验收 |
| 模型服务/参数 | config.Settings、.env.example、model_adapter.request；本地私有 .env | API Base/Key/Model、timeout/retry/max_tokens、指定 tool_choice、兼容结构与异常；Compose/CI 不放真实 Key | B/Q 模拟路径与 L 实际服务分开；evals/README、验证、成本记录 |
| 检索/关联 | retrieval.tokens/search/relations；Workflow.retrieve/generate；semantic.py 是预留 | 前 20 限制、归档语义、排序、真实 IDs、更新/删除；标注集再比较 Embedding | B/Q/E；同集真实评测；RETR-001 与 EVAL 基线 |
| 反馈/候选偏好 | main.reflect/confirm_preference；tools.record_reflection；ORM/DTO；App quests/preferences | 每体验一次结果、explicit/candidates 区分、反馈来源；未来编辑需事务与迁移策略 | B/Q/P/E；DATA-003/AGENT-005 与架构/验证 |
| 测试机制 | pyproject pytest 规则/conftest；Vite/setup 与测试文件；CI | 隔离数据库、Mock 强制、缓存权限、模拟测试与真实评测区别；修改 E2E 要检查目标库 | B/Q/F/P/E 适用项；VERIFICATION 写失败/跳过/未执行 |
| 启动/代理/部署 | scripts、config/db、alembic.ini；Vite、两个 Dockerfile/Compose/Nginx | 开发/容器两个代理、Node/Python 路径、端口、env_file/卷、忽略规则 | S、M/P、D/E；README/VERIFICATION/本手册的命令同步 |

数据库结构真正改变时，从 ORM metadata 生成新 revision、人工检查升级/降级，再在隔离库验证；固定已用的 0001 不作为后续升级补丁。未来命令是 .venv/Scripts/python.exe -m alembic revision --autogenerate -m 描述，必须在已正确配置连接及修改 ORM 后执行；本轮没有生成迁移。现有 M 测试流程在下一节，不会写个人 wonder.db。

## 六、Windows PowerShell 启动与验证命令

### 6.1 环境条件与证据用法

下面是根据脚本、配置及历史验证记录整理的可执行命令，**本轮没有执行安装、应用启动、pytest、前端检查、迁移、Docker 或 Live 调用**。第八节只记录本轮文档/静态检查。以后执行时查看退出码和输出，失败不计为通过；跳过的 PostgreSQL 测试不计为通过。

- 从项目根运行后端命令；Python 支持 >=3.12,<3.14，启动脚本选择 3.12。已有 .venv 和依赖是下述直接调用的前提；首次安装需要可用 uv/Python 及联网能力。
- 前端要求 Node >=22.13.0 与可用 npm。本机有项目内 Node/uv，但它们是被忽略的工具，不会随克隆自带。全局 Node/npm 可能仍指向旧版本；先核对 node --version、npm --version 和 Get-Command node,npm。单纯把 Node 目录加到 PATH 不保证一个引用相邻旧 node.exe 的 npm.cmd 会换用新版本。
- 有正确 Node/npm 时，首次在 frontend 执行 npm ci，按锁文件安装；web.ps1 不负责安装，缺少 Vite 会报清晰错误。后端 dev.ps1 自己运行 uv sync --frozen 和 Alembic。
- 环境变量覆盖 .env；Settings 缓存配置，换模型/数据库后需重启后端。示例 Key 为空且 MOCK_MODE=true；没有 Key 也会使用 Mock。
- 脚本通常可直接运行；若执行策略阻止，可在获准的本地环境用 powershell.exe -NoProfile -ExecutionPolicy Bypass -File 调用对应脚本，参数随后传入。这只影响该进程，不需要更改全局执行策略。

### 6.2 本地 Mock + SQLite 启动

终端一：

```powershell
Set-Location -LiteralPath 'D:\Projects\wonder-orbit'
$env:MOCK_MODE = 'true'
.\scripts\dev.ps1 -Sqlite
```

这会初始化/迁移**个人使用的 wonder.db**，然后运行带 reload 的后端；用于日常使用，不作为隔离测试启动命令。打开 http://127.0.0.1:8000/docs；/api/health 检查数据库及配置模式。

另开终端二，已安装前端依赖：

```powershell
Set-Location -LiteralPath 'D:\Projects\wonder-orbit'
.\scripts\web.ps1 -Port 5173
```

按 Vite 输出打开页面。端口被占时 Vite 可能改用后续端口，不能只凭命令参数断言最终是 5173；改端口还须核对 CORS 和 E2E_BASE_URL。两个服务均可用 Ctrl+C 停止。开发 /api 通过 Vite 转发；未启动后端时前端页面本身可返回 200，但业务请求会失败。

### 6.3 B/Q：后端测试和静态质量

已有 .venv/dev 依赖时，在根目录：

```powershell
Set-Location -LiteralPath 'D:\Projects\wonder-orbit'
New-Item -ItemType Directory -Path .cache -Force | Out-Null
& .\.venv\Scripts\python.exe -m pytest -q -rs
& .\.venv\Scripts\ruff.exe check backend evals
& .\.venv\Scripts\ruff.exe format --check backend evals
```

pytest 配置自带 backend 导入路径和 .cache/pytest 临时目录，但 basetemp 只创建最后一级，全新检出需先创建 .cache，不能依赖 uv 外部缓存。conftest 强制 Mock/空 Key、覆盖 Session，测试用隔离库；普通 pytest 未设置 TEST_POSTGRES_URL 时该项跳过。已有缓存的权限错误须处理环境权限并重跑，不能把初次错误计入通过。可定位回归：

```powershell
Set-Location -LiteralPath 'D:\Projects\wonder-orbit'
& .\.venv\Scripts\python.exe -m pytest backend/tests/test_mvp.py backend/tests/test_acceptance.py backend/tests/test_model_template.py -q -rs
```

可用 uv 命令校验锁而不升级依赖；本机存在项目内 uv 时使用下面路径，普通克隆需将调用换成已安装的 uv：

```powershell
Set-Location -LiteralPath 'D:\Projects\wonder-orbit'
$env:UV_CACHE_DIR = Join-Path (Get-Location).Path '.cache/uv'
& .\.tools\bootstrap\bin\uv.exe lock --check --offline
```

### 6.4 F：前端检查和构建

在确认 Node/npm 满足要求后执行；首次或锁文件变动才需要 npm ci，不必每次检查都重装：

```powershell
Set-Location -LiteralPath 'D:\Projects\wonder-orbit\frontend'
node --version
npm --version
# 依赖尚未安装或锁文件变化时执行：npm ci
npm run format:check
npm run lint
npm run typecheck
npm run test
npm run build
```

format:check 不修改格式；test 是 Vitest，build 包含 tsc -b 和 Vite。构建成功只证明静态构建，不证明 Nginx 部署。各命令分别检查退出码；沙箱子进程 spawn EPERM 是环境失败，须解决后复跑。

若沿用本机已安装的项目内 Node 与 node_modules，可绕开全局旧 npm.cmd，直接运行相同 CLI；下列路径本轮实际检查存在，但命令未重跑：

```powershell
Set-Location -LiteralPath 'D:\Projects\wonder-orbit'
$projectNode = Join-Path (Get-Location).Path '.tools/node/node_modules/node/bin/node.exe'
Push-Location frontend
try {
    & $projectNode node_modules/prettier/bin/prettier.cjs --check src e2e '*.ts' '*.js' '*.json' index.html
    & $projectNode node_modules/eslint/bin/eslint.js .
    & $projectNode node_modules/typescript/bin/tsc --noEmit
    & $projectNode node_modules/vitest/vitest.mjs run
    & $projectNode node_modules/typescript/bin/tsc -b
    & $projectNode node_modules/vite/bin/vite.js build
} finally {
    Pop-Location
}
```

### 6.5 M/P：数据库迁移与 PostgreSQL

SQLite 迁移用新的独立文件，不使用个人 wonder.db；已有 .venv/Alembic 时：

```powershell
Set-Location -LiteralPath 'D:\Projects\wonder-orbit'
New-Item -ItemType Directory -Path '.cache' -Force | Out-Null
$scratchName = 'guide-schema-' + [guid]::NewGuid().ToString('N') + '.db'
$previousDatabaseUrl = $env:DATABASE_URL
try {
    $env:DATABASE_URL = 'sqlite:///./.cache/' + $scratchName
    & .\.venv\Scripts\python.exe -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw 'Alembic upgrade failed' }
    & .\.venv\Scripts\python.exe -m alembic current
    if ($LASTEXITCODE -ne 0) { throw 'Alembic current failed' }
    & .\.venv\Scripts\python.exe -m alembic check
    if ($LASTEXITCODE -ne 0) { throw 'Alembic schema check failed' }
} finally {
    $env:DATABASE_URL = $previousDatabaseUrl
}
```

结果库留在被忽略的 .cache，不自动删除。check 无差异也不等于 downgrade 或 PostgreSQL 已验证。开发新结构时生成新 revision 并审查，只对一次性库验证升级/降级，不能对个人库试回滚。

PostgreSQL 集成测试需要已经启动的**专用测试数据库**，允许创建/删除独立 schema。下面 URL 的用户名/密码是本地占位，必须按自己的隔离服务配置，不指向个人/生产库：

```powershell
Set-Location -LiteralPath 'D:\Projects\wonder-orbit'
$previousPostgresUrl = $env:TEST_POSTGRES_URL
try {
    $env:TEST_POSTGRES_URL = 'postgresql+psycopg://wonder:wonder@localhost:5432/wonder_test'
    & .\.venv\Scripts\python.exe -m pytest backend/tests/test_postgres.py -q -rs --override-ini 'addopts='
} finally {
    $env:TEST_POSTGRES_URL = $previousPostgresUrl
}
```

此测试只检验 ORM create_all 下的 JSON/外键，不覆盖 Alembic。对 PostgreSQL 迁移应另将 DATABASE_URL 指向专用库执行 upgrade/check/current，再验证隔离库 downgrade；这些目标环境检查仍待完成。CI 用自己的 PostgreSQL 服务，不代表本机 URL 中的 wonder_test 已存在。

### 6.6 E：浏览器闭环必须隔离数据

E2E 会真实写 Star/Quest/Reflection/Preference。先停止占用 8000 的旧后端，在单独终端用明确的隔离 SQLite 文件启动；**不要加 -Sqlite**，否则脚本覆盖成个人 wonder.db：

```powershell
Set-Location -LiteralPath 'D:\Projects\wonder-orbit'
New-Item -ItemType Directory -Path '.cache' -Force | Out-Null
$env:DATABASE_URL = 'sqlite:///./.cache/guide-e2e-' + [guid]::NewGuid().ToString('N') + '.db'
$env:MOCK_MODE = 'true'
# 记录此 URL，并确认是当前 8000 服务使用的配置
$env:DATABASE_URL
.\scripts\dev.ps1
```

另开终端启动 web.ps1；确认页面显示 Mock、端口与代理指向该隔离后端。第三个终端，正确 Node/npm、Playwright 已安装且 Chromium 可用时：

```powershell
Set-Location -LiteralPath 'D:\Projects\wonder-orbit\frontend'
# 仅在浏览器尚未安装时执行：npx playwright install chromium
$env:E2E_BASE_URL = 'http://127.0.0.1:5173'
$env:E2E_ALLOW_WRITE = 'true'
try {
    npm run test:e2e
} finally {
    Remove-Item Env:E2E_ALLOW_WRITE -ErrorAction SilentlyContinue
}
```

E2E_ALLOW_WRITE 只表明允许脚本写入，不核验目标 DB；必须人工核对上述服务配置。截图/浏览器临时目录默认在 .cache/e2e，后端日志在启动终端。成功后检查页面异常、移动溢出、截图及真实结果；不能把测试新建的 Mock 数据说成真实个人历史。

### 6.7 D/L：尚未完成目标环境验证的命令

Docker/Compose 需已安装并启动 Docker、端口空闲、联网构建；Compose 要求根 .env，可从空 Key 的示例复制，保留 MOCK_MODE=true。不要覆盖已有私有 .env：

```powershell
Set-Location -LiteralPath 'D:\Projects\wonder-orbit'
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}
docker compose -p wonder-guide-check config --quiet
docker compose -p wonder-guide-check up --build
```

指定 project 名隔离 named volume，不隔离宿主端口。Compose 用数据库 wonder，后端 URL 被 service.environment 指向 db；页面为 http://127.0.0.1:8080。不要自动删卷。本轮和现有记录均没有成功运行 Compose/Nginx 的证据。

Live 本阶段全部 not run，禁止执行。只有下一阶段确认本地配置、明确首次真实请求授权后才使用以下命令（最多一个公开 collect；.env 保留 Mock 默认；先本地填正确北京 Host/Key/Model、MODEL_PROVIDER=bailian、MODEL_MAX_RETRIES=0）：

```powershell
Set-Location -LiteralPath 'D:\Projects\wonder-orbit'
$env:MOCK_MODE='false'
try {
    & .\.venv\Scripts\python.exe evals/run_live.py --allow-live --max-cases 1
} finally {
    $env:MOCK_MODE='true'
}
```

脚本不会再覆盖 MOCK_MODE；缺条件退出且不构造模型。失败停跑、无 SDK 自动重试、不升级型号。只调用 adapter.draft，不导入数据库、不审批，输出被忽略的 .cache/live-eval.json（实际 executed_cases、model、公开 DTO、错误分类、耗时、SDK usage 或 null）。schema_valid 只表示结构合法，不能证明语义质量/完整 Agent 效果；真实服务、免费额度/usage、explore 与审批目标环境证据仍待后续授权。初学者配置词汇、协议/参数与 Token 边界见 [evals/README](../evals/README.md)。

### 6.8 S：PowerShell 语法与运行是两种检查

以下使用**当前终端对应版本**的真实解析器，仅检查文件，不启动服务。可分别在 Windows PowerShell 5.1 和 PowerShell 7 终端运行：

```powershell
Set-Location -LiteralPath 'D:\Projects\wonder-orbit'
foreach ($scriptFile in @('scripts/dev.ps1', 'scripts/web.ps1')) {
    $parseTokens = $null
    $parseErrors = $null
    $fullScriptPath = (Resolve-Path -LiteralPath $scriptFile).Path
    $null = [System.Management.Automation.Language.Parser]::ParseFile(
        $fullScriptPath, [ref]$parseTokens, [ref]$parseErrors
    )
    if ($parseErrors.Count -gt 0) {
        $parseErrors | Format-List
        throw "PowerShell syntax errors in $scriptFile"
    }
    Write-Output "$scriptFile : syntax OK"
}
```

解析通过不证明 Node、依赖、端口或服务正常。本轮也对手册中所有 PowerShell 示例做 ParseInput 检查，**没有执行这些示例**。

## 七、项目状态边界

以下表格为 **UX-003 前的历史快照（2026-10-11 建立，2026-10-17 CI 修复轮局部更新）**，保留其历史验证边界，不作当前状态台账。现已进入 M2 UX-003 首轮文案交付、等待用户体验；CI 成功范围及最新测试见 VERIFICATION，正式任务状态见 Backlog；没有按文件数量计算完成百分比。

| 状态 | 实际范围 | 依据与边界 |
| --- | --- | --- |
| 已实现且有历史本地验证 | Star CRUD/搜索/真实关联、单个可编辑草稿、LangGraph 节点/受控工具、候选检索与约束验证、批准写入、反馈/候选确认、生成重试及审计、八页 Web | 实际源码 + VERIFICATION 的 Mock/SQLite API/规则测试与开发阶段浏览器闭环；后端最近 47 passed、1 PG skipped，前端 9 passed |
| 已实现且有历史工程检查 | SQLite 初始迁移/schema check、Ruff、前端格式/lint/typecheck/build、两版本脚本解析 | VERIFICATION 的分批次证据；本轮不重跑应用检查，不用旧耗时作性能基准 |
| 仍待目标环境完整验证 | PostgreSQL URL/ORM/FK/行锁和可选集成用例；Compose/两个 Dockerfile/Nginx；修复后的远程 CI | 2026-10-17 核对首次远程前端及 PG 迁移/schema 检查通过，但普通 pytest 失败、独立 PG 集成未执行；本地已复现修复。INFRA-001/002/003 尚未完整验收，回滚/并发/容器未验证 |
| 已实现适配路径但真实调用未验证 | ChatOpenAI forced tool、结构/异常分类、Live extraction runner | AGENT-001/EVAL-001；模拟服务测试不代表供应商兼容/效果；health 只查数据库并报告配置模式，不证明 Key 有效或模型服务已连通 |
| 待实现与验收 | UX-003 输入提示、UX-001 首次引导、UX-002 流程衔接、UI-001/002 视觉/陪伴打磨 | 目前有基础提示/占位视觉，三项用户改进尚未完成，不把现有元素视为新方案通过 |
| 计划或暂缓的后续能力 | RETR-001 语义检索及 EVAL 后续标注/比较；并发可靠性、候选编辑等正式待办 | 查看 PRODUCT_BACKLOG 的状态/依赖；semantic.py 只有接口，run_live.py 仅提取案例；暂缓不等于删除 |

当前功能还受单用户、无账号权限隔离、轻量文字模板、支持约束有限、未知预算不能编造等边界限制。审计快照不是逐节点恢复 checkpointer；重试是新运行，审批不是常驻 LangGraph interrupt。参照 Backlog 判断下次做什么，参照 VERIFICATION 判断实际验证过什么。

## 八、如何维护与本轮核对

遇到重要文件新增/删除/重命名、公开符号更名、职责拆分、节点/工具/API/事务变化、代理或启动命令变化时：

1. 先用源码与配置定位真实变更，更新对应索引行/流程段/任务定位/命令，不机械重写整份文档。
2. 核对每个相对 Markdown 文件链接、函数/类所属文件和路由装饰器；移动文件时同时修正链接和文本中的旧路径。
3. 命令根据 package.json、pyproject、脚本/CI 与实际环境重新校对；执行过才能追加日期/环境/结果到 VERIFICATION，语法检查和实际运行分开。
4. 保持代码、架构/学习文档与本手册一致；任务只在 Backlog 改正式状态。新增思想/交付/验收分别更新 IDEA_LOG/CHANGELOG/VERIFICATION，但仍以本次用户允许范围为准。
5. 普通内部局部修改如果未改变导航/职责/接口/命令，不要求改手册；发现旧声明不再成立则修正对应部分，保留状态核对日期。

本轮实际读取全部可提交自有文件；Python 通过 AST 检查符号/路由，JSON/TOML 配置读取验证，前端组件/调用和样式、脚本/容器配置按源码逐项对照。没有读取依赖包内部、个人数据库或运行日志内容。索引包含所有 65 个当前自有文件（含本手册；空 __init__.py、迁移模板与锁文件也列出），不包含运行产物。

本轮交付前实际执行内联检查，结果如下；不创建辅助源码，不导入应用或连接数据库。

| 文档/静态检查 | 实际结果 |
| --- | --- |
| 文件索引 | 覆盖当前 65 个自有文件，无重复/遗漏；所有 67 个本地文件链接存在且位于仓库内 |
| Python/前端符号 | 20 个 Python 文件可 AST 解析；94 处 Python 重要符号引用、33 处前端符号引用与实际定义对应 |
| 路由/命令 | main.py 的全部 22 条路由与表一致；出现的 npm run 脚本均存在；9 个本机工具/CLI 文件路径存在（只检查存在性） |
| PowerShell 实际解析器 | 5.1.26100.9444 与 7.6.5：各检查 14 个手册示例、2 个启动脚本，语法错误均为 0；未执行示例或启动脚本 |
| 文档格式 | UTF-8 可读、代码围栏配对、无尾随空白或替换字符 |
| 修改范围 | 原 64 个文件中只有 AGENTS.md 改变，另新建本手册；63 个其他原文件 SHA-256 未变，无原文件删除 |
| Git | 暂存区为空；65 个项目文件未跟踪；未执行暂存/提交/推送，个人数据库仍被忽略 |

本轮没有安装依赖、重跑业务测试/前端构建、启动服务、迁移数据库、调用真实模型、运行 Docker/远程 CI，也没有修改 VERIFICATION 的历史证据。仅本手册与 AGENTS 的维护规则改变，不执行 git commit/push。
