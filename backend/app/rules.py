"""可解释约束常量；模型得到的模板和后端验证使用同一份定义。"""

SUPPORTED_CONSTRAINTS = {"仅室内", "不购买", "不外出"}
TEXT_STEPS = [
    "读一遍这条星星的原始内容。",
    "写下三个你想进一步了解的问题。",
    "选出最想追问的一个，记录这次感受。",
]

# AGENT-004-A offline-v1：有限文字活动，不声称完成科学核验或设备实验。
DIRECTION_STEPS = {
    "knowledge": [
        "读一遍星星原文，区分用户已提供的信息和仍不知道的事实。",
        "围绕原文写一个想弄清的具体问题，标为待核实，不先猜答案。",
        "为这个问题记下检索词和核实方向：寻找相关研究机构或科普资料，核对出处与证据；本次不联网。",
    ],
    "hands_on": [
        "只用眼前这条星星文字，挑出两个与兴趣有关的词，不需要额外材料或设备。",
        "试着把这两个词按自己关心的先后重新排列，比较哪种顺序更便于继续探索。",
        "在当前输入框中留下选定顺序和一个观察，作为这次文字整理小尝试的产出。",
    ],
    "creative": [
        "从星星原文选一个想表达的主题。",
        "围绕它构思一句短文或一个设计点子，可以自由想象。",
        "留下这份创作；它是创意表达，不是科学解释或事实结论。",
    ],
}


def exploration_steps(direction):
    return DIRECTION_STEPS.get(direction, TEXT_STEPS)


def quest_constraint_errors(proposal, request, pref):
    """Shared pure checks; no database evidence or semantic cost inference."""
    errors = []
    if proposal.estimated_minutes > min(request.available_minutes or pref.max_minutes, pref.max_minutes):
        errors.append("超过时间上限")
    if proposal.estimated_minutes < pref.min_minutes:
        errors.append("少于偏好的最短时间")
    budgets = [b for b in [request.budget, pref.max_budget] if b is not None]
    if budgets and (proposal.estimated_budget is None or proposal.estimated_budget > min(budgets)):
        errors.append("预算未知或超过上限")
    levels = {"low": 1, "medium": 2, "high": 3}
    if any(levels[proposal.energy_level] > levels[e] for e in [request.energy_level, pref.energy_level] if e):
        errors.append("超过精力上限")
    # 自由文本约束不由模型判定；支持的约束也限定为可验证的文字记录模板。
    if pref.constraints:
        if any(c not in SUPPORTED_CONSTRAINTS for c in pref.constraints):
            errors.append("存在未支持的约束，需要用户澄清")
        elif (
            proposal.steps != exploration_steps(request.exploration_direction)
            or proposal.estimated_budget != 0
        ):
            errors.append("约束要求可验证的免费室内文字记录步骤")
    return errors
