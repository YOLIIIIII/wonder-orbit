# 固定检查案例与模型兼容验证

cases.json 保存公开固定输入、Mock 精确期望标签和业务失败场景。backend/tests/test_mvp.py 使用隔离库做确定性断言。Mock 通过率不代表模型准确率。

2026-10-25 第一阶段历史边界：当时只交付接入准备与离线证据，真实模型全部 not run。下文保留该阶段 collect-only 入口说明；第二阶段的独立工作流入口、授权边界与真实失败另见本文末节，不能以历史禁用/成功表述替代当前证据。

## 三种验证分别证明什么

| 方式 | 是否请求模型 | 是否写库 | 能证明什么 |
| --- | --- | --- | --- |
| 日常 Mock | 否 | 页面确认可写当前开发库 | 固定规则和应用流程；没有 LLM 语义理解 |
| 离线兼容 pytest | 否；真实 LangChain/SDK + 内存 MockTransport 或 Fake | API 测试仅 tmp_path 新库 | 实际请求 JSON、工具解析、Pydantic、异常分类、审批隔离；不证明供应商联网成功 |
| 明确授权的 Live runner | 是，可能消耗 Token | 不导入数据库，不审批、不保存 Star/Quest | 实际服务是否返回指定工具和合法草稿；不等于语义质量或完整图评测 |

离线命令（安全，不调用模型）：

```powershell
& .\.venv\Scripts\python.exe -m pytest backend/tests/test_qwen_adapter.py backend/tests/test_live_runner.py -q
```

测试层禁用 .env 读取和 LangSmith tracing，强制空 Key/Mock；专门的 SDK 测试仅传测试 Key 与测试 Host、阻止 DNS/HTTP 建连。Windows TestClient 的事件循环需要 loopback 自唤醒，不能将它误判为模型网络调用。新测试依赖当前锁文件已有的 httpx2 传输实现（OpenAI SDK 3.28.0 使用 httpx2），未新增依赖。默认 pytest/CI/lint/build/E2E 均不运行 Live runner。

## 本地配置：四个名称

- **API Key**：鉴权凭据；仅写本地被忽略的 .env 或环境变量，不贴到对话、源码、截图或 GitHub。
- **API Host**：百炼业务空间显示的专属域名，不含协议和路径；本项目不另建 Host 配置项。
- **Base URL**：`https://` + 实际北京业务空间 API Host + `/compatible-mode/v1`。不要再拼 `/chat/completions`，SDK 会添加。官方当前北京格式是 `https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1`，Key 须属于同地域；离线预检只能检查格式，不能证明真实地域、业务空间或权限。
- **Model ID**：请求中的模型名称，本阶段固定 `qwen3.8-flash`，不是网页展示名称或免费额度名称。

已有 .env 只手动编辑必要行，不要用示例覆盖它。只有文件不存在时才复制 .env.example。以下全部为公开示例，不可直接调用：

```dotenv
MOCK_MODE=true
MODEL_PROVIDER=bailian
MODEL_NAME=qwen3.8-flash
MODEL_API_BASE_URL=https://example.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
MODEL_API_KEY=
MODEL_TIMEOUT=30
MODEL_MAX_RETRIES=0
MODEL_MAX_TOKENS=2048
```

把示例 Host 换成本地控制台中的实际 API Host，把 Key 仅填在本地；继续保留 `MOCK_MODE=true`，不要启动真实模式服务。环境变量会覆盖 .env；若填了 .env 仍被拒绝，先在本机检查是否存在旧变量，勿输出其值。`git check-ignore .env` 应返回文件名，`git ls-files .env` 应无输出；别用 `git add -f`。仓库忽略 .env 变体、.cache、数据库及日志，不提交真实 Host 或私人结果。

唯一新增项 `MODEL_PROVIDER` 是供应商参数的隔离开关，默认 `openai-compatible`，保留原 Mock 和通用 OpenAI 兼容路径；仅 `bailian` + `qwen3.8-flash` 才通过 `extra_body={"enable_thinking": false}` 关闭思考，不添加可任意扩展的参数字典或百炼 SDK。

## 为什么指定工具需要非思考配置

适配器仍调用 `bind_tools([tool], tool_choice=tool_name)`。实际锁定的 langchain-openai 1.7.0 会将名称转为 `{"type":"function","function":{"name":"create_star_draft"}}`（explore 为 generate_quest_proposal）；这不是让模型自由挑工具。Qwen 思考模式对 tool_choice 取值有兼容限制，采用官方非思考示例，保持明确指定函数，不改成 auto/required，也不接受普通文本冒充工具结果。

SDK 将 extra_body 中的 enable_thinking 合并为最终请求 JSON 的顶层字段。适配器固定 Chat Completions 路径；唯一且名称匹配的工具调用、无 invalid_tool_calls、Pydantic 校验全部通过才返回 DTO。多个调用（含一个正常加一个坏 JSON）均失败；工具只提交草稿/候选，模型没有写数据库、SQL、代码或命令执行权。原文/来源以输入覆盖，未提供的兴趣原因仍留空；真实 Star 引用、约束、批准二次校验及幂等仍由现有工作流控制。

另已核对 langchain-openai 会将 MODEL_MAX_TOKENS 对应的 max_tokens 转为实际 JSON 的 max_completion_tokens；百炼当前官方参数表支持 Qwen3.5-Flash 及之后的 Flash，该值不构成精确费用上限。未额外覆写参数，离线测试断言实际字段。超时、限流、服务不可用、非法工具和非法结构继续分开分类，输出不附服务原始错误。

## 下一阶段首次 Live：先确认配置与授权，再执行

**以下命令本阶段未执行；等待用户另行授权。** 仅用于独立脚本，不启动日常后端。保留 .env 的 Mock 默认，通过当前终端临时启用，结束后恢复：

```powershell
$env:MOCK_MODE='false'
try {
    & .\.venv\Scripts\python.exe evals/run_live.py --allow-live --max-cases 1
} finally {
    $env:MOCK_MODE='true'
}
```

先在本地设置正确的 MODEL_PROVIDER、Key、北京 Base URL、MODEL_NAME 与 MODEL_MAX_RETRIES=0。runner 不强制覆盖 Mock；缺授权、空/常见占位 Key、Mock、非法模型/地址、错误地域/示例 Host、重试不为 0 都非零退出。预检不是远程密钥有效性验证，格式正确但无效的 Key 仍会在未来实际请求时报错。

默认 `--max-cases=1`，上述命令最多执行 extraction 的第一个 ocean-space collect 案例（无敏感信息），不遍历全部三个，不含 explore、LangGraph、审批或持久化。SDK 自动重试必须为 0；任一失败立即停止并退出 1，不扩大案例、不切换模型。未来可显式提高正整数上限，最多取固定列表实际存在的条数；本阶段不批量运行。explore/审批的真实证据以后另加，不把此脚本说成完整 EVAL-001。

真实请求可能消耗**输入 Token**（系统提示、工具 Schema、固定文本）和**输出 Token**（工具参数/草稿）；本方案请求关闭思考，是否接受参数、实际 usage 和免费额度扣除仍需真实服务确认。不预估实际 Token 数或费用；用户报告的 100 万免费额度及用完即停未由脚本验证，不应据此无限测试。

结果只写被忽略的 .cache/live-eval.json，包含 mode/provider/model、配置的案例上限/输出上限/重试、实际 executed_cases、各案例 ID/collect、schema_valid 或失败分类、elapsed_ms、通过 Pydantic 的公开结构化输出与 usage。usage 仅取 SDK 返回的 input_tokens/output_tokens/total_tokens 非负整数；缺失为 null，不估算、不当作 0。失败在收到可解析的响应时也可能保留实际 usage；无响应不能凭空得知服务是否已消耗 Token。文件每次覆盖，下一阶段若需比较先在本地保留脱敏副本；不写 Key、Host、Authorization、原始异常、隐藏推理或私人数据。结构合法不等于语义准确，报告仍需人工复核。

2026-10-25 已核对官方资料：[Function Calling](https://help.aliyun.com/zh/model-studio/qwen-function-calling)、[OpenAI 兼容接入](https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope)、[Chat 参数](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions)、[模型 ID](https://help.aliyun.com/zh/model-studio/qwen3-8-flash)。官方文档与本地请求验证不替代真实连通性证据；本轮完整记录见 [VERIFICATION](../docs/VERIFICATION.md#agent-001-phase1-20261025)。


## AGENT-001 第二阶段：隔离库工作流入口与本轮停止结果

新增 `run_workflow_live.py`，复用已有 validate_live_config；通过进程内 FastAPI TestClient 运行实际 LangGraph/ToolRegistry/ModelAdapter 与 decision API，不启动 HTTP 服务。使用显式 --allow-live 后，进程内固定 bailian/qwen3.8-flash/非 Mock/零重试；Key/北京 Base URL 只由 Settings 运行时读取，不展示/改写 .env、不改变模型请求代理。适配器 request 与实际 bind_tools.invoke 都限制 collect→explore 各一次，调用前落盘尝试；任何失败占次数并停跑，不能通过更换模型或批次参数扩额度。

入口会新建 `.cache/qwen-workflow-随机值/workflow.db`，拒绝已有/越界目标，核对实际 engine/SessionLocal、Alembic 版本及 Star/Quest/Reflection 初始为零。collect 先验证原文/来源和未知字段，未批准不入档；只有通过才在隔离库发明确的测试批准、重复决定验证幂等。然后先只读检索确定能命中真实测试 Star，再发 explore，核对来源、时间/零预算/低精力/固定免费室内文字步骤；只有合法候选才测试批准一个 Quest、幂等与关联。没有候选就部分失败，不造候选；不写 Reflection。所有测试决定都标记为 isolated_test_simulation，不能表述为用户实际批准/完成体验。

复用命令如下，**本轮已经因真实语义检查失败停止，不得再执行；后续任何新请求需另行授权**：

```powershell
& .\.venv\Scripts\python.exe evals/run_workflow_live.py --allow-live
```

每次显式执行会创建新的库和 report.json，调用尝试、公开 DTO/节点/工具、计数、实际 usage/耗时保留于被忽略目录，不上传个人结果。缺省运行在读取 Settings 前拒绝，默认 pytest/CI/lint/build/E2E 不触发该命令。输出过滤实际 Key/Host，禁用该专用过程的日志/tracing；环境临时覆盖退出恢复。个人 wonder.db 只做前后文件哈希。

离线保护测试（不联网）可运行：

```powershell
& .\.venv\Scripts\python.exe -m pytest backend/tests/test_workflow_live_runner.py -q
```

本轮真实结果：只请求 collect **1 次**，唯一 create_star_draft、Pydantic 及 understand_request→extract_star_draft→await_user_decision 成功；模型把原文主题片段填入 interest_reason，未满足未知动机 null 要求，入口以 collect_unknown_fields 在批准前停止。实际 input=1038/output=207/total=1245 Token，invoke=10119ms；Star/Quest/Reflection 最终均零（停止后额外 mode=ro 核对），explore/审批幂等全部 not run，没有用第二次额度重跑。现有“原文子串”保护不能区分主题与动机，未改 Prompt/生产逻辑或降低验收；AGENT-001 继续 in_progress，不代表真实闭环通过。完整证据见 [本轮验证](../docs/VERIFICATION.md#agent-001-workflow-20261025)。


<a id="interest-reason-offline-20261025"></a>

## interest_reason 语义边界修正（2026-10-25，仅离线）

本轮真实模型请求 **0**；没有使用此前未消耗次数，也没有运行任何 --allow-live 命令。上一节真实 1245 Token/collect_unknown_fields 为历史证据，保留不改；本节不是新真实审批/explore 结果。

interest_reason 仅表达用户明确说出的个人兴趣原因。collect 专用提示给正反例和 null 规则；实际适配器在 Pydantic 之后，除原文子串外，还要求原因完整对应同一句明确个人因果片段。有限支持：`我喜欢/我对…感兴趣，因为/由于…`（可带少量程度词）、`因为/由于…，所以/因此我…`、`…让我/使我对…产生兴趣`。主题、科学因果而未指向个人兴趣、目标/时间安排、否定/不确定/引述、原文之外或改写/片段证据不保留。仅将该字段在 missing_fields 中统一为未知一次、已知时移除；其他字段/提问不重写。

保守规则是有边界的句式白名单，不是通用中文语义模型。复杂长句、隐含/跨句动机、改写原因、引号和否定混合表达可能漏提取；没有充分证据优先 null，用户仍能在既有草稿编辑中明确填写。空/空白字符串、null、字段缺失归 null；错误类型继续由 Pydantic 拒绝为 invalid_model_output，不强转成字符串。

公开回归夹具 [interest_reason_cases.json](interest_reason_cases.json) 有 30 个对照，包含历史原文/错误 reason（期望仍 null）、用户列明的正反例及证据范围/空值/非法类型；通过真实 LangChain/SDK 内存传输，不发 HTTP。Fake API/图回归确认标准化后的草稿仍 await_user_decision，批准前无 Star/Quest；没有降低 runner 的 unknown_fields 或审批规则。旧“主题复述导致失败”断言迁为“主题复述被清空且审批前零记录”，非法工具/结构和其他未知字段编造仍要求失败。

```powershell
& .\.venv\Scripts\python.exe -m pytest backend/tests/test_qwen_adapter.py backend/tests/test_workflow_live_runner.py -q
```

这只是字段契约回归，不启动 EVAL-001、不提供模型准确率。category/tags/description 和其他 missing_fields 名称的历史质量观察留给 EVAL-001 候选，未在本轮修正。真实 Prompt 接受情况、修正后的真实 collect/审批/explore，仍需下一次明确授权；本轮结束即停止。证据见 [本轮验证](../docs/VERIFICATION.md#agent-001-reason-20261025)。

2026-11-01 真实复验追加：最新语义代码下仅执行一次现有工作流 runner，collect/explore 各一次全通过（共 2869 Token），原始动机 null、隔离库模拟批准/幂等/真实来源/约束/关联通过，最终 Star/Quest/Reflection=1/1/0。单一服务验收已具证，不代表模型质量基线或真实体验效果；历史失败保留。两次额度用完，本轮停止，任何新调用需新授权。详见 [最新实证](../docs/VERIFICATION.md#agent-001-live-recheck-20261101)。


<a id="offline-quality-v1"></a>

## EVAL-001 第一阶段：公开质量规范与离线检查（2026-11-01）

[QUALITY_RUBRIC](QUALITY_RUBRIC.md) 定义 Collect 7 项、Explore 5 项人工 0/1/2 标准；确定性检查独立统计，未知/不可观察保留 not_rated，不自动给低分或高分。

案例账本：旧 cases.json 3 个 extraction + 7 个 scenarios，旧 interest_reason_cases.json 30 个对照均不变；新增 [quality_cases.json](quality_cases.json) **10 个**综合评价案例，共 **50 个文件内案例条目（原 40 + 新 10）**，部分主题/规则复用，不称 50 个独立语义样本。新增案例版本 wonderorbit-cases-v1，规范 wonderorbit-quality-v1；每项附输入、规则、人工关注点。明确动机复用旧 personal-documentary，无批量复制 30 个对照。

无需 .env、数据库或网络，直接执行：

```powershell
& .\.venv\Scripts\python.exe evals/check_results.py --results evals/sample_fake_results.json
```

仅输出 JSON 至 stdout；需要保存时可将标准输出重定向到明确的公开 JSON 文件。不自动读取 .cache、历史报告、私人配置或 wonder.db；拒绝 .cache/.git/.env 路径及非 JSON。输入必须由调用者确认 public_data=true；这不是自动隐私脱敏器，不向输入文件放私密数据。

结果封装参考 [sample_fake_results.json](sample_fake_results.json)。必填 format_version=offline-results-v1、public_data=true、case_version、rubric_version、mode（fake/mock/live）、results；生成版本 prompt_version/workflow_version/retrieval_version 缺失写 not_recorded，model 缺失写 unknown。一个文件只表示一种模型/模式/版本组合；比较时分别运行、保留 metadata，不混合成绩；未知或不同案例/规范版本拒绝评价。

每条结果用 case_id、status=executed/not_run；执行输出放 output（现有 DraftResult 或 ProposalResult 原始公开 DTO）。缺案例计 not_run；缺输出或非法 Schema 失败。manual 按规范维度保存 {"score": 0/1/2/"not_rated", "note": "简短依据"}；给分必须有备注。缺评分保留 not_rated。审批观察可选 approval={before,after_generation,after_decision,after_repeat,decision,authorization}，计数只针对本次对应实体（Collect 的 Star / Explore 的 Quest）；decision=approved/rejected/none，authorization=user_api/isolated_test_simulation/none。未提供观察标 not_rated，不从文本推断权限。公开案例 ID 与输出基于固定检索快照验证，不查询正式数据库。

报告含各案例实际检查与人工字段、版本、模式、证据类型及两套计数。Fake 标记 tool_self_test，Mock 标记 application_mock，Live 标记 supplied_live_output_unverified：工具只评价所提供输出，不能证明它来自供应商。人工未评分不算确定性失败；退出 0 不等于完整评价通过。退出 1 为确定性失败，2 为输入/版本错误（错误信息不回显输入）。手写样例只执行一个 Collect，其他九项 not_run，人工均 not_rated；它不是 Qwen 质量基线。

本轮真实模型请求 0；AGENT-001 既有真实闭环结论不变。EVAL-001 只交付第一阶段，正式状态见 Backlog；完整真实输出/人工质量基线、Prompt 对比与真实体验效果均未采集。本轮禁止运行上述历史 Live 命令，交付后停止。


## EVAL-001 第二阶段：审核公开结果的离线准备

本入口只准备人工审核过的公开 capture，不发请求、不导入 Settings/数据库/适配器/工作流，不搜索或读取 `.cache`/`.env`/私人历史报告；输出到 stdout，不自动保存。仍使用上面的质量 v1 和同一份 `quality_cases.json`，不新建评分器。`public_data=true` 是提交者的审核声明，不能由程序证明数据来自供应商或已人工脱敏。

已有工具边界：`run_live.py` 只跑旧 `cases.json.extraction` 的 collect，报告没有新固定集输入/检索快照且旧 v1 标识不能证明实际源码版本；`run_workflow_live.py` 仅固定深海闭环、隔离库 UUID、输入也与新固定集不完全相同。两者都不能直接改 case_id 就当作固定质量基线。本轮未改 runner、未执行真实调用；历史深海的未分类/机械描述/复述三问，只是探索性观察，不能填成新集结果或人工分数。未来固定集 Live 采集仍需另行明确调用额度和接入授权。

### 对应关系与数据格式

完整可运行格式见 [sample_public_captures.json](sample_public_captures.json)：两个**手写 Fake 自测夹具**（Collect 复用旧 fake 样例、Explore 复用离线测试内容），UUID 为合成映射示例，不是历史 Qwen 输出。`fixture-only-v1` 仅标识自测数据，不能用作真实生成版本。

| Capture 字段 | 与固定案例/输出的关系 |
| --- | --- |
| 顶层 `format_version` | `public-captures-v1`；准备后变为既有 `offline-results-v1` |
| `public_data`、`mode`、`model` | 审核声明、fake/mock/live 证据类型、实际模型标识；live 标签仍未验证供应商来源 |
| `case_version`、`rubric_version` | 必须与固定文件及检查器一致，ID 不重命名、不按主题猜测匹配 |
| `prompt_version`、`workflow_version`、`retrieval_version` | 必须明确非空且非 unknown/not_recorded；每条 capture.generation_versions 必须完全相同。推荐用实际采集源码 SHA256 + 提交 SHA，不能从当前代码倒推旧生成版本 |
| `case_id`、`status` | 同一案例批次最多一次；executed 必须有 capture；缺条目/not_run 保持未执行 |
| `capture.observation_layer` | `adapter_dto` 或 `workflow_dto`；分别表示适配器结果/工作流公开 DTO。不是原始 HTTP 响应或隐藏推理；比较时必须同层 |
| `capture.input` | 与案例 input 逐字段相同，包含来源/引用/时间预算精力。不能只复制文本、忽略来源 |
| `capture.preferences` | 与案例 preferences 相同；没有则 `{}`，不能使用个人偏好 |
| `capture.retrieved_stars` | 实际传给本层生成的公开检索内容，字段集合与固定快照相同，star_id 保留运行时 ID；不能只提供标题/ID 而无原文/分类/标签 |
| `capture.id_map` | 运行时 ID→公开 Star ID 一一对应；必须覆盖且仅覆盖本案例检索集，内容也要一致。Collect/空检索为 `{}` |
| `capture.raw_output` | Collect 为 DraftResult，Explore 为 ProposalResult；原样保留所选 DTO 层的值，缺输出为 null，不能编造输出 |
| `manual`、`approval` | 沿用原结果格式和外部审批证据；缺评分保留 not_rated，未观察到审批不从模型文本推断 |

所有字段直接见样例，未知字段拒绝。必须先由人确认只含公开数据；不要把私人历史缓存换个名字导入。新入口会拒绝已带 normalized output 的 capture，避免两份结果打架。

### UUID 映射与保真边界

程序要求映射无重复目标、无缺失/额外检索项，并逐字段核对实际公开内容与固定检索快照；不能凭 UUID、标题或主题相近认定同源。只转换合法 ProposalResult 内 `based_on_star_ids` 的精确 ID 元素；标题/说明/rationale/步骤等文本、顺序和重复项不改。原始 DTO、原始运行 ID、映射和观察层保留在准备结果的 `capture` 中，检查报告也保留；再次检查会重新计算并拒绝归一化结果与原始证据漂移。程序不查询库，不能证明调用者提供的 ID 或快照真由数据库产生。

若实际工作流使用的 Star 内容或输入不同（包括先 collect 的真实草稿与固定 fixture 不同），不能无损归到该案例，本工具直接拒绝。不要伪造一致性、补齐成预期字段或将科学主题近似看成同一输入。应另获授权后在隔离库设置匹配的公开 fixture，记录真实 UUID/实际提供的快照再采集；实际执行检索得到额外/缺失项时保留失败，不手工删改来过检查。运行 API 的其他字段可在人工选取 DTO 前另行存公开旁证，不能悄悄改变模型实际看到的内容。

源码核对到的具体缺口：`workflow.retrieve/generate` 传给 `ModelAdapter.proposals` 的排序检索项含 `text/score/match_basis`，text 是 description 或 original_text；`star_details` 虽读取，但并未作为该生成方法的 stars 参数。固定质量案例目前是 `original_text/category/tags` 快照。因此当前真实工作流 payload 与 fixture **不等价**，本轮明确不提供自动工作流报告转换，也不把 text 改名当原文或删除额外字段来蒙混。本离线映射可用于未来明确选择 adapter_dto 层、实际向适配器提供固定公开快照的采集；完整 workflow_dto 接入仍需先另行定义/版本化实际检索快照并离线核对，再获真实采集授权。已有 runner 仍只证明既定历史闭环。样例的两个 UUID/映射只是验证这种转换方法，不证明现有工作流已经兼容固定集。

非法 DTO 保留不修复，仍由现有检查器报告 output_schema failed；executed 缺输出报告 failed。错误引用或映射/上下文/版本不匹配则准备失败 exit 2，输出通用错误，不回显输入。准备 exit 0 仅表示转换完成，不代表质量通过；人工缺分既不算 0 也不算 passed。

### 本轮可安全执行的自测与未来人工评审

仅运行公开 Fake 样例，不运行上文历史 Live 命令：

```powershell
# stdout 是准备好的结果封装；显式按 UTF-8 保存，避免 Windows 重定向编码差异。
.venv/Scripts/python.exe -X utf8 evals/check_results.py --prepare-captures evals/sample_public_captures.json
# 已审核的真实 capture 将来走同一入口，但需要先有独立真实采集授权。
```

若要保存再检查，可用 Python subprocess 捕获 stdout，并以 `Path(...).write_text(text, encoding="utf-8")` 写入明确的公开 JSON 路径（不要存 `.cache` 再交给此工具，也不要覆盖输入）；随后 `python evals/check_results.py --results <公开准备结果.json>`。原始 capture/准备结果/检查报告都应保留，以便追溯 ID 与版本；本工具不自动发布文件。

人工步骤：先核对案例输入、真实生成版本/模型/观察层和检索来源，再看确定性失败，然后按 [QUALITY_RUBRIC](QUALITY_RUBRIC.md) 在准备结果 `manual` 填 0/1/2 和具体依据，未审项保留 not_rated。不要编辑 capture/raw_output 来“修正”模型；要修模型另开有版本的新批次。无建议场景不能观察的质量维度继续 not_rated。最后重跑原 `--results`，逐项看结果和备注，不将缺执行/缺评分解释成高质量，不跨观察层或版本合并分数。

## EVAL-001 第三阶段 A：固定 adapter_dto 采集入口

`collect_quality.py` 复用 ModelAdapter.draft/proposals、run_live.validate_live_config 与原检查器。默认只读取公开固定案例、schemas/rules，输出离线计划；不导入 Settings/模型/图/数据库、不读 .env。不修改生产 Prompt/规则，也不执行 LangGraph、检索 API 或审批。真实配置仅在显式真实运行时由现有 Settings 读取；不能将 .env/Key/私人 Host 放入命令行、报告或对话。

本轮可执行（零请求）：

```powershell
.venv/Scripts/python.exe -X utf8 evals/collect_quality.py
```

固定顺序 explicit-motivation（Collect）、unknown-motivation（Collect）、grounded-explore（Explore）。案例 wonderorbit-cases-v1、规范 wonderorbit-quality-v1；脚本对整个 quality_cases.json 仅将 CRLF 转为 LF，再计算固定 SHA256（同时作为公开检索快照版本）；LF/CRLF 等价，其他字节改动仍拒绝。Explore 原样提供 original_text/category/tags 等完整字段，不冒充 workflow 的 text/score/match_basis。公开 public-star-ocean 映射至测试合成 UUID `00000000-0000-4000-8000-000000000001`，严格一一对应，绝非数据库记录。偏好 `{}` 展开为现有 Preferences 默认值，约束为空；请求默认字段和完整 adapter_inputs/model_payload 均保存供复核。

以下为**阶段 B 单独确认后的固定命令，本轮禁止执行**：

```powershell
.venv/Scripts/python.exe -X utf8 evals/collect_quality.py --allow-live
```

预检只接受百炼北京 qwen3.8-flash、非 Mock、非空 Key、合法业务空间地址、SDK retries=0；预检不验证 Key/余额。适配器 request 双保护：全批最多 3 次且每例一次；请求前持久化 attempted_unknown 与计数，超时/断网/非法结构均已消耗一次尝试，失败立即停止。禁用本调用 tracing，不保存响应正文/headers/隐藏推理。没有补跑、重试、换模型、探针或可扩充案例参数。

结果固定为被忽略的 `.cache/quality-baseline-v1/raw.json`，`public_data=false`。首次创建批次目录，已存在即拒绝（包括中断或失败留下的目录）；不提供覆盖/恢复开关，也不要删除目录后用剩余额度重跑。本轮尚未创建真实批次。保存实际 Git SHA + dirty 标记、适配器/DTO/规则/采集脚本/预检/案例/规范/检查器 SHA256；仅 source_hashes 中的 evals/quality_cases.json 使用上述规范化哈希，suite_hash_normalization=crlf-to-lf，其余文件仍为真实字节 SHA256；prompt_version 是适配器源码哈希，workflow_version=not_executed:adapter_dto，retrieval_version 是固定公开快照哈希。后处理 DTO 保留原值，这是现有适配器/Pydantic/动机防护后的观察层，不能反推未经防护的原始模型内容。

每次记录 schema_valid/failed/attempted_unknown、脱敏 failure_type、实际 SDK usage 或字符串 unknown、elapsed_ms；中断未完成耗时为 null。不能将 schema_valid 当成人工质量合格。raw_output 是实际合法 DTO；非法结构没有合法 DTO 时保留 null 与错误类别，不重构/修复成预期结果。合法 DTO 的错误来源会保留原始记录且停止，准备工具仍拒绝映射，不能放宽检查器。

人工复核与后续离线链路：

1. 人工查看 raw.json，逐项确认只含公开内容（包括模型生成文字）、真实版本/模型/观察层、三个实际参数及 model_payload、合成映射、尝试/失败/usage。不要修改原始 DTO；若出现敏感输出，停止导出，另行处置，不自动上传。
2. 人工确认公开后，运行 `.venv/Scripts/python.exe -X utf8 evals/collect_quality.py --export-reviewed-public`。该开关即人工已完成内容审核的声明，程序无法代替人工审查。仅读取该固定批次，校验来源/上下文/版本后，以新文件方式导出 `evals/reviewed_quality_captures.json`、public_data=true；已有目标拒绝覆盖。mode=fake/mock 的原始记录拒绝冒充真实采集。导出不调用模型、不上传。
3. `.venv/Scripts/python.exe -X utf8 evals/check_results.py --prepare-captures evals/reviewed_quality_captures.json`。将 stdout 按 UTF-8 保存为另一明确公开 JSON，再用原 `--results <公开结果.json>`；详见上一节的 subprocess 保存方式。原始 capture 保留，只有 ID 的规范化映射改变 output。
4. 按 QUALITY_RUBRIC 共同填人工 0/1/2 和依据；缺评分继续 not_rated。审批未执行，保留空审批观察/检查 not_rated，不编造计数。失败类别随 Result.failure_type 留在报告，未采案例为 not_run；usage/耗时/实际 payload 随 sampling 旁证保留。live 仍标 supplied_live_output_unverified，离线工具不能证明供应商来源；Fake 自测不是质量基线。

阶段 A 实证见 [VERIFICATION](../docs/VERIFICATION.md#eval-001-phase3-a-20261101)。真实请求 0；完整正式基线与内容评分未执行，EVAL-001 状态仅见 Backlog。

2026-11-01 跨平台修复：固定案例哈希为 `f4e90c1783d0cf4168f5f833ac2e87d5e2b29aebb990e95fb74392337488dea4`，plan、采样记录及 export_reviewed 共用 CRLF→LF 规则；导出也校验当前案例文件，实质修改继续拒绝。未对全项目规范化、未关闭版本保护。旧版若留下基于 CRLF 字节哈希的记录，本修复不改写/迁移，也不删除或重置既有采样目录；其旧哈希不会被冒充为新规范化版本。历史失败与本地验证见 [修复记录](../docs/VERIFICATION.md#eval-001-hash-fix-20261101)。

## 2026-11-06：首批已审核公开 Qwen 证据

用户于采样记录时间 2026-11-01 执行三次 qwen3.8-flash；本轮整理新增调用 0。生成 SHA=e0afb6277ac0160683e17915408bf6176218c2f0，dirty=false；案例 wonderorbit-cases-v1、规范 wonderorbit-quality-v1；adapter_dto，workflow/审批未执行。8 个源码/规范哈希、完整公开输入/实际 payload 与 ID 映射均已核对，原始文件未修改。工具仍标 supplied_live_output_unverified，离线检查不能独立认证供应商来源。

- [公开 capture](reviewed_quality_captures.json)：审核后通过原导出入口生成，保留实际公开 DTO/运行时合成 ID/参数/usage，不含个人库或密钥。
- [正式准备结果](reviewed_quality_results.json)：原 --prepare-captures 输出，仅规范化引用 ID；人工仅 grounded-explore.exploration_value=1，note 标记用户选择来源。其余分数均 not_rated，助手候选仅存旁证文档。
- [确定性报告](reviewed_quality_report.json)：原 --results 生成，20 passed / 1 failed / 7 not_run / 3 not_rated（审批）。人工全案例维度统计 1 rated / 59 not_rated；三条已执行案例共 19 维，仅一维用户确认，其余 18 维未正式评分。不计算总分或合格率。

本批三次 usage 逐项核对为输入3426、输出778、共4204 Token；耗时3601/2926/8904ms。explicit-motivation 的 estimated_budget 原值0.0与期望null不符，**报告退出码1是保留的真实发现**，不得改输出或检查器来消除。另两个案例现有确定性项通过；标题三分钟/实际八分钟属于人工发现，未被现有检查器覆盖。其余七例 not_run，缺审批观察 not_rated；三条 schema_valid 不等于整理充分或体验有价值。保留历史失败，不宣称 EVAL 全部完成。

可完全离线重查（stdout 应以 Python subprocess 按 UTF-8 捕获，exit 1 预期）：

```powershell
.venv/Scripts/python.exe -X utf8 evals/check_results.py --results evals/reviewed_quality_results.json
```

已存在的公开文件与原采样目录不得用导出命令覆盖/重建。本轮未修改 Prompt/规则/案例版本；原始输出、唯一正式用户评分、候选评分理由和未来方向见 [本批验证与初评](../docs/VERIFICATION.md#eval-001-first-baseline-20261106)。
