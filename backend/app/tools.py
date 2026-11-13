from time import perf_counter
from sqlalchemy import select
from fastapi import HTTPException
from .learning import validate_learning_result
from .models import AgentRun, Quest, QuestStar, Reflection, Star, UserPreference
from .retrieval import search, star_dict
from .rules import quest_constraint_errors
from .schemas import (
    AgentRequest,
    DetailArgs,
    EmptyArgs,
    DraftResult,
    Preferences,
    ProposalArgs,
    ValidateArgs,
    PersistArgs,
    ReflectionArgs,
    SearchArgs,
)


class ToolRegistry:
    """显式允许列表；未经审批调用写工具会被拒绝。无 eval、SQL 字符串或系统命令。"""

    def __init__(self, session, adapter, run: AgentRun, approved: bool = False):
        self.session, self.adapter, self.run, self.approved = session, adapter, run, approved
        self.registry = {
            "search_stars": (SearchArgs, self.search_stars, False),
            "get_star_details": (DetailArgs, self.get_star_details, False),
            "get_user_preferences": (EmptyArgs, self.get_user_preferences, False),
            "create_star_draft": (AgentRequest, self.create_star_draft, False),
            "generate_quest_proposal": (ProposalArgs, self.generate_quest_proposal, False),
            "validate_quest_proposal": (ValidateArgs, self.validate_quest_proposal, False),
            "persist_approved_quest": (PersistArgs, self.persist_approved_quest, True),
            "record_reflection": (ReflectionArgs, self.record_reflection, True),
        }

    def call(self, name: str, args: dict):
        start = perf_counter()
        event = {"kind": "tool", "name": name, "status": "running"}
        try:
            if name not in self.registry:
                raise HTTPException(400, "未知工具")
            schema, handler, requires_approval = self.registry[name]
            parsed = schema.model_validate(args)
            if requires_approval and not self.approved:
                raise HTTPException(403, "正式写入需要用户明确批准")
            result = handler(parsed)
            event["status"] = "succeeded"
            return result
        except Exception:
            event["status"] = "failed"
            raise
        finally:
            event["elapsed_ms"] = round((perf_counter() - start) * 1000)
            self.run.events = [*self.run.events, event]

    def search_stars(self, args):
        return search(self.session, args.query, args.category, args.include_archived)

    def get_star_details(self, args):
        star = self.session.get(Star, args.star_id)
        if not star:
            raise HTTPException(404, "星星不存在")
        data = star_dict(star)
        return {key: value for key, value in data.items() if key not in {"created_at", "updated_at"}}

    def get_user_preferences(self, _):
        preference = self.session.get(UserPreference, 1)
        return Preferences.model_validate(preference.explicit if preference else {}).model_dump()

    def create_star_draft(self, request):
        return DraftResult.model_validate(self.adapter.draft(request)).model_dump(mode="json")

    def generate_quest_proposal(self, args):
        return validate_learning_result(
            args.request, self.adapter.proposals(args.request, args.stars, args.preferences)
        ).model_dump(mode="json")

    def validate_quest_proposal(self, args):
        proposal, request, pref = args.proposal, args.request, args.preferences
        errors = []
        if not set(proposal.based_on_star_ids).issubset(args.allowed_ids):
            errors.append("引用了未检索到的星星")
        if any(not self.session.get(Star, sid) for sid in proposal.based_on_star_ids):
            errors.append("引用的星星已不存在")
        errors.extend(quest_constraint_errors(proposal, request, pref))
        return {"valid": not errors, "errors": errors}

    def persist_approved_quest(self, args):
        existing = self.session.scalar(select(Quest).where(Quest.proposal_key == args.proposal_key))
        if existing:
            return {"quest_id": existing.id}
        data = args.proposal.model_dump()
        star_ids = data.pop("based_on_star_ids")
        if any(not self.session.get(Star, sid) for sid in star_ids):
            raise HTTPException(409, "依据星星已删除，请重新生成")
        quest = Quest(**data, proposal_key=args.proposal_key, status="accepted")
        self.session.add(quest)
        self.session.flush()
        for sid in set(star_ids):
            self.session.add(QuestStar(quest_id=quest.id, star_id=sid))
        return {"quest_id": quest.id}

    def record_reflection(self, args):
        quest = self.session.get(Quest, args.quest_id)
        if not quest:
            raise HTTPException(404, "探索不存在")
        if quest.status != "accepted":
            raise HTTPException(409, "体验已有结果")
        reflection = Reflection(quest_id=quest.id, **args.reflection.model_dump())
        self.session.add(reflection)
        quest.status = args.reflection.outcome
        self.session.flush()
        preference = self.session.get(UserPreference, 1)
        if not preference:
            preference = UserPreference(id=1, explicit={}, candidates=[])
            self.session.add(preference)
        # 只由明确 liked_aspects 提供候选类别；不自动写入 explicit。
        candidates = [*preference.candidates]
        for aspect in args.reflection.liked_aspects:
            if aspect.strip():
                candidates.append(
                    {
                        "id": f"{reflection.id}:{len(candidates)}",
                        "category": aspect.strip(),
                        "summary": f"你在反馈中写下喜欢：{aspect.strip()}",
                        "reflection_id": reflection.id,
                        "source": "user_feedback",
                        "confirmed": False,
                    }
                )
        preference.candidates = candidates
        return {"reflection_id": reflection.id, "quest_id": quest.id}
