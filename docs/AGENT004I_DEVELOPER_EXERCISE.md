# AGENT-004-I 研发学习记录与练习

## 理解实际调用链

AgentRequest 表示这一次探索的输入和限制（例如 budget=0）；Preferences 是用户明确偏好的长期上限（例如 max_budget=0）。Proposal 是模型提出、尚未审批的 Quest 候选，estimated_budget 可以是已知数或未知 None。

ModelAdapter.proposals → Workflow 生成/来源门控 → 校验 → app.rules.quest_constraint_errors(proposal, request, pref) → 用户确认 API → 正式 Quest。纯规则只返回错误列表，不调用模型、不查数据库、不自动保存。编辑和批准仍有服务端检查；本练习聚焦其中预算边界，并不替代完整审批测试。

实际代码：[rules.py](../backend/app/rules.py)；相近测试：[test_learning_quality_v3.py](../backend/tests/test_learning_quality_v3.py) 中 test_budget_and_readonly_diagnostics / test_shared_rules。后者所在文件已有 pytest、Proposal、AgentRequest、Preferences 和 quest_constraint_errors 导入，也有 proposal(**changes) 工厂。

## 你亲自填写

把下列函数加到 **backend/tests/test_learning_quality_v3.py** 的末尾。骨架只在本文提供，尚未加入测试集，避免把未完成练习算成通过。

```python
@pytest.mark.parametrize("budget", [0, None, 1])
def test_zero_budget_quest_user_exercise(budget):
    candidate = proposal(estimated_budget=budget)
    request = AgentRequest(request_type="explore", text="海洋", budget=0)
    preferences = Preferences(max_budget=0)
    errors = quest_constraint_errors(candidate, request, preferences)
    # TODO 1：根据 budget 填出 expected_rejected（0允许；None和1拒绝）。
    expected_rejected = ...
    # TODO 2：亲自断言“预算未知或超过上限”是否在 errors 中，
    #         并与 expected_rejected 比较。不要只检查函数没有报异常。
```

你需要填写 expected_rejected 的表达式和核心 assert；无需改生产规则。先预测三个参数的结果，再运行。若三例均通过，说明明确免费与未知费用被区分；不代表模型会正确填写费用，也不证明引用的 Star 存在。

在项目根目录 PowerShell 只运行此练习：

```powershell
.venv/Scripts/pytest.exe backend/tests/test_learning_quality_v3.py::test_zero_budget_quest_user_exercise -q
```

当前尚未添加该函数，直接运行会提示找不到测试，这是预期。已有全量回归不计为你完成练习。

## 本轮学到什么

历史实验完整性应比较当时的证据和记录哈希；当前回归检查当前协议和业务规则。Fake SDK 测试不等于重放 G 模型。Prompt 是行为目标，纯规则是确定性边界；表达与布局改善需要与真实 Agent 语义质量分开验收。

## 2026-11-18 用户完成练习的追加记录

用户已亲自在backend/tests/test_learning_quality_v3.py添加test_zero_budget_quest_user_exercise，填写expected_rejected与核心assert。提交前审阅实际使用 `.venv/Scripts/python.exe -B -m pytest backend/tests/test_learning_quality_v3.py::test_zero_budget_quest_user_exercise -q -p no:cacheprovider -o addopts=` 定向运行，结果 **3 passed**。函数区分0明确免费与None未知、1超过零预算；本轮不改用户断言。

前文“尚未添加函数”是I阶段教学安排的历史事实，保留原文；当前练习已经完成。定向3 passed不等同于重新运行完整套件，最终交付全量结果单独记录于VERIFICATION。
