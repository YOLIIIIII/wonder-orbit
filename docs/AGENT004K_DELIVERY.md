# AGENT-004-K · 补充材料再探索

2026-11-23（Asia/Shanghai）。M3 穿插 M2；本地实现，等待用户产品验收。开始 HEAD 与用户基线均为 `f51b5b70ce707a9bc22da098b07fc59963ab0a77`，工作区干净。任务状态只在 [Backlog](PRODUCT_BACKLOG.md) 维护；本轮证据见 [VERIFICATION](VERIFICATION.md#agent-004-k-20261123)。

## 实际变更

- `App.tsx / LearningResult`：请求与运行均为 Explore、方向 knowledge、状态 succeeded/awaiting_decision/decided/failed 且无 learning_card 时提供入口；不匹配中文错误。覆盖材料不足、来源门控移除卡片、无材料及失败结果；running、Collect、其他方向、有卡片不显示。
- `startReplenishing`：仅从 `run.state.request` 预填问题、learning_source.text/label/url、时间、预算、精力；进入既有 Explore 表单并将焦点交给问题输入。可替换材料与来源、修改问题与约束；知识方向固定。
- 复用表单/API、现有防重复提交和幂等键；材料必填、空白拒绝、长度检查、URL 限 http/https，浏览器原生校验与中文提示。显示用户材料未经独立核实、URL不访问、补充后仍可能无法回答。取消返回原 Run，只发生读取。
- 提交后显示新结果，历史原 Run 保留；不发 parent_run_id，不新增关系字段、表、迁移、材料版本或聊天系统。未改 backend 业务逻辑、J 的 resolve_continuation、Schema、来源引用/位置门控、预算 None/0、Quest 审批规则。
- `test_replenishment.py`：三种不足状态 × None/0预算，捕获适配层入参、新根运行、原运行不变、幂等、无正式Quest、J拒替换；`App.test.tsx`：四种结束状态与不适用入口；`replenishment-preview.mjs`：双尺寸真实隔离Mock API流程。

## 模块03：一次真实调用会发生什么

1. 打开、编辑或取消：仅 React 状态变化；取消时 GET 原 Run。不 POST，不创建 Run，不调用模型。
2. 明确点击提交：`App.tsx` 表单 → `generate` → `POST /api/agent/runs`，沿用随机幂等键。`AgentRequest`（backend/app/schemas.py）接收 `request_type=explore`、`exploration_direction=knowledge`、修改后的 `text`、完整本次 `learning_source={text,label,url}`、`available_minutes`、`budget`、`energy_level`。**没有 parent_run_id**；默认 source_type/source_reference 仍由既有 Schema 处理。
3. `main.py:create_run / resolve_continuation / begin_run`：Schema 验证在先，根请求跳过父关系解析；通过后先持久化新的独立 Run，再执行 Workflow。非法请求不创建 Run；同键同请求复用原结果，不再次生成。
4. `workflow.py:retrieve / generate`：用本次问题检索当前真实 Star，读取当前明确 Preferences，经 `tools.py:generate_quest_proposal` 传给 `ModelAdapter.proposals`。不读取原 Run 的模型内容。
5. `model_adapter.py:ModelAdapter.proposals / request`：接收新问题、新材料、当前 Star 摘要与明确偏好；计算 `effective_limits={minutes,budget,energy}`。Live 模式在前置规则通过后才向模型发送含上述 request、stars、preferences、effective_limits、可选 constraint_template 的上下文，以及既有系统提示/知识来源约束与结构化输出工具 Schema。无相关 Star、不支持的约束、时间冲突可在调用前返回，故新 Run 不必然有模型调用。**本轮 Mock 不会请求 Qwen。**
6. `learning.py:validate_learning_result` 校验引用/位置/来源元数据，既有 Quest 规则校验后保存新结果；正式 Quest 仍由用户确认 API 授权。

不得自动进入新原始材料的内容：上次 takeaway、interest_relevance、discovery、解释、Quest、模型建议的问题；也不拼入旧运行日志、隐藏推理、密钥或抓取的URL页面。新材料由用户亲自提交；输入是原材料的可编辑副本，不是版本继承关系。旧 AI 输出仍在旧 Run，新 AI 输出只属于新 Run。有效引用不能证明科学结论正确。

## 体验与学习

为什么用户需要：遇到材料不足后可直接修改材料继续探索，减少重复填写，不把补充变成作业。

Agent 解决什么：明确新一次执行的证据来源和用户提交边界，避免把模型旧回答循环当成事实，同时保留 J 的受控父关系。

学到什么：无卡片结果是可以恢复的产品状态；恢复表单是 UI/UX 工程，原始证据选择与独立执行边界是 Agent 工程。本轮没有改变真实模型的相关性、忠实度或拒答能力。

## 验收边界

真实 Qwen 0 请求；不修改 .env、不访问个人正式数据库、不重放 G/v3、不 commit/push、不联网抓取。G-03 语义无关问题仍属于后续真实质量评测。PostgreSQL/完整容器、真实Qwen稳定拒答和用户产品验收仍未验证。

下一步仅为用户验收本次恢复流程；不自动开始新开发或采样。整体 AGENT-004/EVAL-001 不因本轮切片交付宣称完成。


## 预览与文件清单

- [桌面恢复表单](../.cache/agent004k/K-edit-1440-true.png)、[移动恢复表单](../.cache/agent004k/K-edit-390-true.png)、[桌面结果](../.cache/agent004k/K-result-1440-true.png)、[移动结果](../.cache/agent004k/K-result-390-true.png)。截图为固定Mock，不能证明真实Qwen质量。
- 产品实现：[App.tsx](../frontend/src/App.tsx)；测试：[App.test.tsx](../frontend/src/App.test.tsx)、[test_replenishment.py](../backend/tests/test_replenishment.py)、[replenishment-preview.mjs](../frontend/e2e/replenishment-preview.mjs)。
- 文档：本报告、IDEA_LOG、PRODUCT_BACKLOG、PROJECT_GUIDE、VERIFICATION、ROADMAP、CHANGELOG。未增加依赖，未修改.env或后端业务文件。

最终检查：pytest470 passed/1 skipped（PG未配置）/1既有warning，Ruff check/format通过；前端96 passed、lint/typecheck/build/format全部通过；smoke/J/K双尺寸隔离Mock通过，smoke的真实故障fixture明确skip。历史22份哈希检查通过。Git为原基线HEAD，暂存区空，8个已跟踪文件修改、3个新增，无commit/push；详细日志与初轮失败修正记录见VERIFICATION。


## 2026-11-23 · 用户体验与本轮交付授权追加

以上“待用户验收/不commit push”为K初次交付快照。用户已亲自体验无原材料的补充流程，确认入口可发现、问题预填正确、操作流畅；已有原材料后的补充尚未人工体验。自动化结果仍以各次实际日志为准。

遗留体验问题：无知识材料时Mock仍可能生成“找到一份入门材料”Quest及接受按钮，与知识优先/独立行动价值原则存在冲突；本轮未修复、不扩大K、不重写Quest系统，也未解决G-03。

本轮最新授权是在完整审阅/回归通过后，仅提交已核对的11个文件，一次原子commit并正常push origin/main，核实远程CI；不得force push或部署。提交SHA、实际CI URL/Job终态在推送后保存至本地忽略目录.cache/agent004k-final/delivery-result.json并在最终报告提供，不为回填自身SHA追加第二个提交。本轮收尾证据见[验证记录](VERIFICATION.md#agent-004-k-final-20261123)。
