import hashlib
import json
from time import perf_counter
from typing import Annotated
from uuid import uuid4
from fastapi import Depends, FastAPI, Header, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .config import settings
from .db import get_session
from .model_adapter import ModelAdapter, ModelFailure
from .models import AgentRun, Quest, QuestStar, Reflection, Star, UserPreference, now
from .retrieval import record_dict, relations, search, star_dict
from .schemas import AgentRequest, Decision, Preferences, Proposal, ReflectionInput, StarInput
from .workflow import Workflow, finish_run

app = FastAPI(title="WonderOrbit · 星屿", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings().cors_origins.split(","),
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Idempotency-Key"],
)
DB = Annotated[Session, Depends(get_session)]
Key = Annotated[str | None, Header(alias="Idempotency-Key", max_length=100, min_length=1)]


def require(session, model, id):
    record = session.get(model, id)
    if not record:
        raise HTTPException(404, "记录不存在")
    return record


def run_dict(run):
    return record_dict(run)


def quest_dict(session, quest):
    data = record_dict(quest)
    data.pop("proposal_key")
    data["based_on_star_ids"] = list(
        session.scalars(select(QuestStar.star_id).where(QuestStar.quest_id == quest.id))
    )
    reflection = session.scalar(select(Reflection).where(Reflection.quest_id == quest.id))
    data["reflection"] = record_dict(reflection) if reflection else None
    return data


def begin_run(session, kind, payload, key):
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    key = key or str(uuid4())
    existing = session.scalar(select(AgentRun).where(AgentRun.request_key == key))
    if existing:
        if existing.request_hash != digest or existing.request_type != kind:
            raise HTTPException(409, "幂等键已用于其他请求")
        if existing.status == "running":
            raise HTTPException(409, "请求正在执行，若进程中断可使用重试接口")
        if existing.status == "failed":
            raise HTTPException(
                409,
                {
                    "message": "此幂等请求此前已失败，请查看运行记录；生成流程可使用重试接口",
                    "error_type": existing.error_type,
                    "run_id": existing.run_id,
                },
            )
        return existing, False
    config = settings()
    run = AgentRun(
        request_key=key,
        request_hash=digest,
        request_type=kind,
        model_name="mock-rules-v1" if config.effective_mock else config.model_name,
        mode="mock" if config.effective_mock else "live",
        events=[],
        decisions={},
        state={"request": payload},
    )
    session.add(run)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(409, "重复请求，请查询运行记录") from exc
    return run, True


def adapter():
    return ModelAdapter(settings())


def execute_run(session, run, request):
    start = perf_counter()
    try:
        Workflow(session, adapter(), run).execute(request)
    except Exception as exc:
        session.rollback()
        run = require(session, AgentRun, run.run_id)
        run.status = "failed"
        run.error_type = exc.kind if isinstance(exc, ModelFailure) else type(exc).__name__
        run.summary = "本次生成失败，未创建正式星星或探索。可以重试。"
        finish_run(run, start)
        session.commit()
        raise HTTPException(
            502, {"message": run.summary, "error_type": run.error_type, "run_id": run.run_id}
        ) from exc
    finish_run(run, start)
    session.commit()
    return run_dict(run)


@app.get("/api/health")
def health(session: DB):
    session.execute(text("SELECT 1"))
    return {"status": "ok", "mock_mode": settings().effective_mock, "version": "0.1.0"}


@app.get("/api/stats")
def stats(session: DB):
    categories = session.execute(select(Star.category, func.count()).group_by(Star.category)).all()
    return {
        "stars": session.scalar(select(func.count()).select_from(Star)),
        "quests": session.scalar(select(func.count()).select_from(Quest)),
        "completed": session.scalar(
            select(func.count()).select_from(Quest).where(Quest.status == "completed")
        ),
        "categories": [{"name": name, "count": count} for name, count in categories],
    }


@app.get("/api/stars")
def list_stars(session: DB, q: str = "", category: str | None = None, status: str | None = None):
    if q:
        ids = [match["star_id"] for match in search(session, q, category)]
        statement = select(Star).where(Star.id.in_(ids))
    else:
        statement = select(Star)
        if category:
            statement = statement.where(Star.category == category)
    if status:
        statement = statement.where(Star.status == status)
    return [star_dict(s) for s in session.scalars(statement.order_by(Star.created_at.desc()))]


@app.get("/api/stars/{star_id}")
def get_star(star_id: str, session: DB):
    return star_dict(require(session, Star, star_id))


@app.post("/api/stars", status_code=201)
def create_star(data: StarInput, session: DB):
    # 用户手动提交表单即是明确写入；模型无法调用此 API。
    star = Star(**data.model_dump())
    session.add(star)
    session.commit()
    return star_dict(star)


@app.put("/api/stars/{star_id}")
def update_star(star_id: str, data: StarInput, session: DB):
    star = require(session, Star, star_id)
    for key, value in data.model_dump().items():
        setattr(star, key, value)
    session.commit()
    return star_dict(star)


@app.delete("/api/stars/{star_id}", status_code=204)
def delete_star(star_id: str, session: DB):
    star = require(session, Star, star_id)
    if session.scalar(select(QuestStar).where(QuestStar.star_id == star_id).limit(1)):
        raise HTTPException(409, "这颗星星已被探索引用；可归档，保留体验依据")
    session.delete(star)
    session.commit()
    return Response(status_code=204)


@app.get("/api/search")
def search_stars(session: DB, q: str):
    return search(session, q)


@app.get("/api/relations")
def get_relations(session: DB):
    return relations(session)


@app.post("/api/agent/runs", status_code=201)
def create_run(request: AgentRequest, session: DB, key: Key = None):
    run, fresh = begin_run(session, request.request_type, request.model_dump(mode="json"), key)
    return execute_run(session, run, request) if fresh else run_dict(run)


@app.get("/api/agent/runs")
def list_runs(session: DB):
    return [
        run_dict(r) for r in session.scalars(select(AgentRun).order_by(AgentRun.started_at.desc()).limit(50))
    ]


@app.get("/api/agent/runs/{run_id}")
def get_run(run_id: str, session: DB):
    return run_dict(require(session, AgentRun, run_id))


@app.post("/api/agent/runs/{run_id}/retry")
def retry_run(run_id: str, session: DB):
    run = require(session, AgentRun, run_id)
    if run.request_type not in {"collect", "explore"} or run.status not in {"failed", "running"}:
        raise HTTPException(409, "只允许重试失败或中断的生成流程")
    if run.status == "running":
        from datetime import timezone
        from .models import now

        started = (
            run.started_at.replace(tzinfo=timezone.utc) if run.started_at.tzinfo is None else run.started_at
        )
        if (now() - started).total_seconds() < max(120, settings().model_timeout * 4):
            raise HTTPException(409, "运行仍可能在执行，请稍后重试")
    request = AgentRequest.model_validate(run.state["request"])
    # 重试创建新记录；保留失败运行作为历史，不重放任何批准写入。
    new_run, _ = begin_run(session, run.request_type, request.model_dump(mode="json"), None)
    return execute_run(session, new_run, request)


@app.post("/api/agent/runs/{run_id}/decision")
def decide(run_id: str, data: Decision, session: DB):
    run = session.scalar(select(AgentRun).where(AgentRun.run_id == run_id).with_for_update())
    if not run:
        raise HTTPException(404, "运行不存在")
    if run.status not in {"awaiting_decision", "decided"}:
        raise HTTPException(409, "当前运行不可审批")
    index = str(data.index) if run.request_type == "explore" else "star"
    fingerprint = hashlib.sha256(data.model_dump_json().encode()).hexdigest()
    if index in run.decisions:
        decision = run.decisions[index]
        if decision["fingerprint"] != fingerprint:
            raise HTTPException(409, "该候选已有不同的决定")
        return decision
    if run.request_type == "collect":
        if data.index != 0 or data.edited_proposal is not None:
            raise HTTPException(422, "草稿审批参数无效")
    elif run.request_type == "explore":
        if data.index >= len(run.state.get("proposals", [])) or data.edited_star is not None:
            raise HTTPException(422, "候选索引或参数无效")
    else:
        raise HTTPException(409, "当前请求不是候选审批")
    result = {"approved": data.approved, "fingerprint": fingerprint, "decided_at": now().isoformat()}
    if data.approved:
        workflow = Workflow(session, adapter(), run, approved=True)
        if run.request_type == "collect":
            star = data.edited_star or StarInput.model_validate(run.state["draft"]["draft"])
            request = AgentRequest.model_validate(run.state["request"])
            # 原始来源保持可追溯；编辑的是结构化字段。
            star.original_text = request.text
            star.source_type, star.source_reference = request.source_type, request.source_reference

            def persist_star():
                record = Star(**star.model_dump())
                session.add(record)
                session.flush()
                return {"star_id": record.id}

            result.update(workflow.approved_operation("persist_approved_result", persist_star))
        else:
            proposal = data.edited_proposal or Proposal.model_validate(run.state["proposals"][data.index])
            preferences = workflow.tools.call("get_user_preferences", {})
            check = workflow.tools.call(
                "validate_quest_proposal",
                {
                    "proposal": proposal.model_dump(),
                    "request": run.state["request"],
                    "preferences": preferences,
                    "allowed_ids": [s["star_id"] for s in run.state["related_stars"]],
                },
            )
            if not check["valid"]:
                session.commit()  # 保留失败验证审计，不写正式结果。
                raise HTTPException(422, check["errors"])
            result.update(
                workflow.approved_operation(
                    "persist_approved_result",
                    lambda: workflow.tools.call(
                        "persist_approved_quest",
                        {"proposal": proposal.model_dump(), "proposal_key": f"{run_id}:{index}"},
                    ),
                )
            )
    run.decisions = {**run.decisions, index: result}
    total = len(run.state.get("proposals", [])) if run.request_type == "explore" else 1
    run.status = "decided" if len(run.decisions) >= total else "awaiting_decision"
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(409, "已收到相同候选的并发确认，请刷新记录") from exc
    return result


@app.get("/api/quests")
def quests(session: DB):
    return [quest_dict(session, q) for q in session.scalars(select(Quest).order_by(Quest.created_at.desc()))]


@app.put("/api/quests/{quest_id}")
def edit_quest(quest_id: str, data: Proposal, session: DB):
    quest = require(session, Quest, quest_id)
    if quest.status != "accepted":
        raise HTTPException(409, "已有反馈的体验不可编辑")
    origin_run_id = quest.proposal_key.rsplit(":", 1)[0]
    run = require(session, AgentRun, origin_run_id)
    workflow = Workflow(session, adapter(), run, approved=True)
    check = workflow.tools.call(
        "validate_quest_proposal",
        {
            "proposal": data.model_dump(),
            "request": run.state["request"],
            "preferences": workflow.tools.call("get_user_preferences", {}),
            "allowed_ids": [s["star_id"] for s in run.state["related_stars"]],
        },
    )
    if not check["valid"]:
        session.commit()
        raise HTTPException(422, check["errors"])
    values = data.model_dump()
    ids = values.pop("based_on_star_ids")
    for key, value in values.items():
        setattr(quest, key, value)
    for link in session.scalars(select(QuestStar).where(QuestStar.quest_id == quest_id)):
        session.delete(link)
    session.flush()
    for sid in set(ids):
        session.add(QuestStar(quest_id=quest_id, star_id=sid))
    session.commit()
    return quest_dict(session, quest)


@app.post("/api/quests/{quest_id}/reflections", status_code=201)
def reflect(quest_id: str, data: ReflectionInput, session: DB, key: Key = None):
    require(session, Quest, quest_id)
    run, fresh = begin_run(session, "reflection", {"quest_id": quest_id, **data.model_dump()}, key)
    if not fresh:
        return run_dict(run)
    start = perf_counter()
    try:
        result = Workflow(session, adapter(), run, approved=True).approved_operation(
            "process_reflection",
            lambda: Workflow(session, adapter(), run, approved=True).tools.call(
                "record_reflection", {"quest_id": quest_id, "reflection": data.model_dump()}
            ),
        )
        run.status, run.summary = "succeeded", "用户反馈已保存；候选偏好等待用户确认"
        run.state = {**run.state, "result": result}
        finish_run(run, start)
        session.commit()
    except Exception as exc:
        failed_events = list(run.events)
        session.rollback()
        run = require(session, AgentRun, run.run_id)
        run.events = failed_events
        run.status, run.error_type, run.summary = "failed", type(exc).__name__, "反馈保存失败"
        finish_run(run, start)
        session.commit()
        raise
    return run_dict(run)


@app.get("/api/preferences")
def preferences(session: DB):
    pref = session.get(UserPreference, 1)
    return {
        "explicit": Preferences.model_validate(pref.explicit if pref else {}).model_dump(),
        "candidates": pref.candidates if pref else [],
    }


@app.put("/api/preferences")
def put_preferences(data: Preferences, session: DB):
    pref = session.get(UserPreference, 1)
    if not pref:
        pref = UserPreference(id=1, explicit={}, candidates=[])
        session.add(pref)
    pref.explicit = data.model_dump()
    session.commit()
    return preferences(session)


@app.delete("/api/preferences", status_code=204)
def clear_preferences(session: DB):
    pref = session.get(UserPreference, 1)
    if pref:
        session.delete(pref)
        session.commit()
    return Response(status_code=204)


@app.post("/api/preferences/candidates/{candidate_id}/confirm")
def confirm_preference(candidate_id: str, session: DB):
    pref = require(session, UserPreference, 1)
    candidate = next((c for c in pref.candidates if c["id"] == candidate_id), None)
    if not candidate:
        raise HTTPException(404, "候选偏好不存在")
    explicit = Preferences.model_validate(pref.explicit)
    explicit.categories = list(dict.fromkeys([*explicit.categories, candidate["category"]]))
    explicit = Preferences.model_validate(explicit.model_dump())
    pref.explicit = explicit.model_dump()
    pref.candidates = [c for c in pref.candidates if c["id"] != candidate_id]
    session.commit()
    return preferences(session)


@app.delete("/api/preferences/candidates/{candidate_id}", status_code=204)
def remove_candidate(candidate_id: str, session: DB):
    pref = require(session, UserPreference, 1)
    pref.candidates = [c for c in pref.candidates if c["id"] != candidate_id]
    session.commit()
    return Response(status_code=204)
