# 固定检查案例与模型兼容验证

cases.json 保存公开固定输入、Mock 精确期望标签和业务失败场景。backend/tests/test_mvp.py 使用隔离库做确定性断言。Mock 通过率不代表模型准确率。

2026-10-25：AGENT-001 第一阶段只交付接入准备与离线证据，所有真实模型检查 **not run**。本阶段禁止运行下方 Live 命令，不使用真实 Key、免费 Token 或个人 wonder.db。

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
