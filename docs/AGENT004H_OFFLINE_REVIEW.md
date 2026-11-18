# AGENT-004-H 离线发现互动复核 · 2026-11-18

本轮为可运行产品切片与固定 Mock 预览，等待用户体验验收。真实 Qwen 请求 **0**，不把 Mock 内容当模型改善证据。HEAD 保持 aad9ddba7ab7b6c4b0cb6aacb477584344dbb0b0；G 的未提交采样代码、文档与原始结果保留。

## 用户可体验的变化

可以只读知识卡片就结束：knowledge 没有候选时复用已有 succeeded 状态，不产生审批动作；有卡片摘要为“知识内容已生成，无待审批候选”，无卡片摘要为“本次知识探索已结束，无待审批候选”，并保留具体不足说明。其他方向和 Collect 的审批状态不变；旧 awaiting_decision Run 仍按原状态读取，不迁移数据库。

LearningCard 可选 discovery={question,reveal}，长度、非空、字符串类型、额外字段均严格校验；旧 JSON 缺字段可读取。问题与来源先显示；揭晓后显示答案、完整解释、延伸和原文/限定折叠入口。原生 button 支持 Enter/Space、aria-expanded/aria-controls、可见焦点，收起时仍保留按钮焦点。状态仅在 React 中保存，刷新后重新隐藏；不保存用户答案、偏好、Reflection 或 Quest，不触发 API。

Prompt 按“回答兴趣问题→有理解价值的信息→可选有依据的猜测揭晓→独立体验价值才给 Quest”排序，允许仅 learning_card、proposals=[]、questions=[]。持续观察、自愿创作或明确小体验可保留 Quest；复述、分类、列问题没有独立收获。受约束安全模板不变，纯文字 Quest 可明确预算0，未知仍为null且被零预算约束拒绝，后端没有null转0。

## 材料内容人工观察（助手，不代填用户评分）

A：evals/knowledge_preview_material.json 原文字节不变。问题询问鱼诱饵与鱿鱼发光液是否同一用途，未在问题泄露答案；揭晓对照“吸引猎物/迷惑捕食者”，捕食/防御区别均在材料内。完整解释给出化学反应、某些体系的荧光素参与和酶催化，并保留不同体系不能推广的限定。解释以机制为重点，揭晓以用途为重点，不安排笔记，不生成正式 Quest。

B：弱观察只呈现周一三次记录与观察条件未知，没有创造发光机制，没有低价值 Quest。C：固定无关面包输入返回无卡片、无 Quest，简短说明不支持当前探索。D：限定与冲突仍保留；无 discovery 的卡片沿用解释布局。E：无材料方向保留现有获取材料建议，仍需用户审批。

**无关材料限制**：C 仅证明固定 Mock 边界与空结果通路。Prompt 已要求按语义判断、不把否定句中的主题词当证据；没有新增关键词过滤器。真实 Qwen 对 G-03 类材料是否稳定拒绝、是否忠实揭晓、是否填写0预算，均未验证。精确引用校验只能证明字符与来源元数据匹配，不能证明 discovery 语义正确或来源真实。

## 本地证据

- [桌面问题](../.cache/agent004h/A-1440-before.png)、[桌面揭晓](../.cache/agent004h/A-1440-revealed.png)
- [移动问题](../.cache/agent004h/A-390-before.png)、[移动揭晓](../.cache/agent004h/A-390-revealed.png)、[移动原文展开](../.cache/agent004h/A-390-expanded.png)
- [原始Mock预览](../.cache/agent004h/preview.json)、[浏览器日志](../.cache/agent004h/browser.txt)、[后端检查](../.cache/agent004h/pytest.txt)
- 实际结果和跳过项见 [VERIFICATION](VERIFICATION.md#agent-004-h-20261118)。截图与缓存只在本地，不提交。

## 复盘与后续

为什么用户需要：了解知识本身就应有收获，继续参与由用户决定。Agent系统解决什么：消除“生成一定要有可审批任务”的输出与状态耦合；DTO和引用保护是确定性边界，Prompt只是生成目标引导。点击揭晓属于 UI/UX 改进，不是模型能力提升。

学到什么：合法DTO、精确引用与真正的体验价值不同；无需动作的结果应明确完成，而不能伪造候选或追问；科学解释和揭晓需要分别人工核对。G四例、12,369 Tokens和预算失败结论原样保留，不能用H覆盖。

当前仍M3穿插M2；AGENT-004/EVAL-001整体仍in_progress。无新增已证实P0；剩余P1为UX-003、INFRA-001/002、EVAL-001。下一项仅建议用户体验本切片；未来真实验证需要新的独立授权与新批次，本轮停止，不commit/push/发布。
