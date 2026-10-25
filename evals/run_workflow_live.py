"""显式授权、最多两次 Qwen invoke 的隔离库 API/图工作流验证。"""

import argparse
from contextlib import ExitStack
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import sys
import tempfile
from threading import Lock
from time import perf_counter
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))
from app.config import Settings
from app import config as config_module, model_adapter as adapter_module
from app.model_adapter import ModelAdapter, ModelFailure
from app.schemas import DraftResult, ProposalResult
from run_live import validate_live_config

ROOT = Path(__file__).resolve().parents[1]

COLLECT_TEXT = "我一直想了解深海生物为什么会发光，想找时间记录三个感兴趣的问题。"
EXPLORE_REQUEST = {
    "request_type": "explore",
    "text": "深海生物为什么会发光",
    "available_minutes": 10,
    "budget": 0,
    "energy_level": "low",
}
TEST_PREFERENCES = {
    "min_minutes": 1,
    "max_minutes": 10,
    "max_budget": 0,
    "energy_level": "low",
    "constraints": ["仅室内", "不购买", "不外出"],
}
TOOLS = ("create_star_draft", "generate_quest_proposal")


class CheckFailure(Exception):
    """仅携带固定检查分类，不包含服务异常或私人配置。"""


def require(condition, kind):
    if not condition:
        raise CheckFailure(kind)


def file_hash(path):
    if not path.exists():
        return None
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def write_report(path, report, config=None):
    from urllib.parse import urlsplit

    secrets = []
    if config is not None:
        secrets.append(config.model_api_key)
        try:
            secrets.append(urlsplit(config.model_api_base_url).netloc)
        except ValueError:
            pass

    def redact(value):
        if isinstance(value, dict):
            return {key: redact(item) for key, item in value.items()}
        if isinstance(value, list):
            return [redact(item) for item in value]
        if isinstance(value, str):
            for secret in secrets:
                if secret:
                    value = value.replace(secret, "[redacted]")
        return value

    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(redact(report), ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


class CallBudget:
    """分别限制适配器 request 与实际 bind_tools.invoke；失败的 invoke 也占额度。"""

    def __init__(self, report, save, guard):
        self.report, self.save, self.guard = report, save, guard
        self.lock = Lock()
        self.requests = 0

    def enter_request(self, name):
        with self.lock:
            require(self.requests < 2 and name == TOOLS[self.requests], "adapter_call_limit_or_order")
            self.guard()
            self.requests += 1
            self.report["adapter_requests"] = self.requests

    def invoke(self, inner, name, messages):
        with self.lock:
            calls = self.report["calls"]
            require(len(calls) < 2 and name == TOOLS[len(calls)], "invoke_limit_or_order")
            self.guard()
            item = {"tool_name": name, "status": "attempted", "usage": None, "elapsed_ms": None}
            calls.append(item)
            # 在实际 invoke 前落盘；超时/中断没有免费重试机会。
            self.save()
        start = perf_counter()
        try:
            message = inner.invoke(messages)
            item["status"] = "response_received"
            item["returned_tool_names"] = [call["name"] for call in message.tool_calls]
            item["invalid_tool_calls"] = len(message.invalid_tool_calls)
            usage = message.usage_metadata or {}
            counts = {
                key: usage[key]
                for key in ("input_tokens", "output_tokens", "total_tokens")
                if type(usage.get(key)) is int and usage[key] >= 0
            }
            item["usage"] = counts or None
            return message
        except Exception:
            item["status"] = "invoke_failed"
            raise
        finally:
            item["elapsed_ms"] = round((perf_counter() - start) * 1000)
            self.save()

    def factory(self, original):
        budget = self

        class RestrictedChat:
            def __init__(self, **kwargs):
                require(
                    kwargs.get("model") == "qwen3.8-flash"
                    and kwargs.get("max_retries") == 0
                    and kwargs.get("use_responses_api") is False
                    and kwargs.get("extra_body") == {"enable_thinking": False},
                    "model_parameters",
                )
                self.model = original(**kwargs)

            def bind_tools(self, tools, *, tool_choice):
                require(
                    len(tools) == 1 and tools[0]["function"]["name"] == tool_choice, "forced_tool_definition"
                )
                inner = self.model.bind_tools(tools, tool_choice=tool_choice)

                class Bound:
                    def invoke(self, messages):
                        return budget.invoke(inner, tool_choice, messages)

                return Bound()

        return RestrictedChat


def run_workflow(config, directory, report, save, chat_factory):
    """仅由显式授权的 main 调用；离线测试提供 Fake Chat，生产 API/图不替换。"""
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import func, select, text
    from sqlalchemy.orm import sessionmaker
    from fastapi.testclient import TestClient

    validate_live_config(config)
    require(config.model_provider == "bailian" and config.model_name == "qwen3.8-flash", "qwen_config")
    cache = ROOT / ".cache"
    require(
        cache.resolve() == cache
        and directory.resolve().is_relative_to(cache)
        and directory.resolve() != cache
        and not directory.is_symlink(),
        "database_directory",
    )
    database = directory / "workflow.db"
    require(not database.exists() and not database.is_symlink(), "database_must_be_new")
    database.touch(exist_ok=False)
    isolated = config.model_copy(update={"database_url": "sqlite:///" + database.as_posix()})
    environment = {
        "DATABASE_URL": isolated.database_url,
        "MOCK_MODE": "false",
        "MODEL_PROVIDER": "bailian",
        "MODEL_NAME": "qwen3.8-flash",
        "MODEL_MAX_RETRIES": "0",
        "LANGSMITH_TRACING": "false",
        "LANGCHAIN_TRACING_V2": "false",
        "LANGCHAIN_TRACING": "false",
    }
    with ExitStack() as stack:
        stack.enter_context(patch.dict(os.environ, environment))
        stack.enter_context(patch.object(config_module, "settings", lambda: isolated))
        db_module = importlib.import_module("app.db")
        main_module = importlib.import_module("app.main")
        from app.models import Star, Quest, Reflection

        engine = db_module.make_engine(isolated.database_url)
        stack.callback(engine.dispose)
        stack.enter_context(patch.object(db_module, "engine", engine))
        stack.enter_context(
            patch.object(db_module, "SessionLocal", sessionmaker(engine, expire_on_commit=False))
        )
        stack.enter_context(patch.object(main_module, "settings", lambda: isolated))

        def guard():
            require(
                db_module.engine is engine
                and engine.url.get_backend_name() == "sqlite"
                and Path(engine.url.database).resolve() == database.resolve()
                and db_module.SessionLocal.kw["bind"] is engine
                and not main_module.app.dependency_overrides,
                "actual_engine_mismatch",
            )

        guard()
        migration = Config(str(ROOT / "alembic.ini"))
        migration.set_main_option("path_separator", "os")
        migration.set_main_option("script_location", str(ROOT / "backend/migrations"))
        command.upgrade(migration, "head")
        with engine.connect() as connection:
            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        report["isolation"] = {
            "database": str(database.relative_to(ROOT)),
            "actual_engine_verified": True,
            "alembic_revision": revision,
        }

        def counts():
            guard()
            with db_module.SessionLocal() as session:
                return {
                    name: session.scalar(select(func.count()).select_from(model))
                    for name, model in (("stars", Star), ("quests", Quest), ("reflections", Reflection))
                }

        def check_counts(expected, kind):
            current = counts()
            report["counts"][kind] = current
            require(current == dict(zip(("stars", "quests", "reflections"), expected)), kind)
            save()

        def record_exit_counts():
            report["counts"]["on_exit"] = counts()
            save()

        stack.callback(record_exit_counts)
        check_counts((0, 0, 0), "initial")
        budget = CallBudget(report, save, guard)

        class ObservedAdapter(ModelAdapter):
            def request(self, name, schema, payload):
                budget.enter_request(name)
                try:
                    result = super().request(name, schema, payload)
                    report["calls"][-1]["validated_output"] = result.model_dump(mode="json")
                    return result
                except ModelFailure as exc:
                    if report["calls"]:
                        report["calls"][-1]["adapter_error_type"] = exc.kind
                    raise
                finally:
                    save()

        stack.enter_context(patch.object(adapter_module, "ChatOpenAI", budget.factory(chat_factory)))
        stack.enter_context(patch.object(main_module, "adapter", lambda: ObservedAdapter(isolated)))

        with TestClient(main_module.app, raise_server_exceptions=False) as client:
            require(
                client.put("/api/preferences", json=TEST_PREFERENCES).status_code == 200, "test_preferences"
            )

            def generate(kind, payload):
                before = len(report["calls"])
                start = perf_counter()
                response = client.post(
                    "/api/agent/runs", json=payload, headers={"Idempotency-Key": "isolated-" + kind}
                )
                stage = {
                    "api_status": response.status_code,
                    "api_elapsed_ms": round((perf_counter() - start) * 1000),
                }
                report["stages"][kind] = stage
                body = response.json()
                run_id = body.get("run_id") or body.get("detail", {}).get("run_id")
                if run_id:
                    run = client.get("/api/agent/runs/" + run_id).json()
                    stage["run"] = {
                        key: run[key]
                        for key in (
                            "run_id",
                            "mode",
                            "model_name",
                            "status",
                            "error_type",
                            "events",
                            "state",
                            "elapsed_ms",
                        )
                    }
                save()
                require(response.status_code == 201, kind + "_generation_failed")
                require(len(report["calls"]) == before + 1, kind + "_invoke_count")
                require(
                    body["mode"] == "live"
                    and body["model_name"] == "qwen3.8-flash"
                    and body["status"] == "awaiting_decision",
                    kind + "_run_state",
                )
                require(all(event["status"] == "succeeded" for event in body["events"]), kind + "_events")
                nodes = {event["name"] for event in body["events"] if event["kind"] == "node"}
                tools = {event["name"] for event in body["events"] if event["kind"] == "tool"}
                expected_nodes = (
                    {"understand_request", "extract_star_draft", "await_user_decision"}
                    if kind == "collect"
                    else {
                        "understand_request",
                        "load_preferences",
                        "retrieve_related_stars",
                        "generate_suggestions",
                        "validate_suggestions",
                        "await_user_decision",
                    }
                )
                expected_tools = (
                    {"create_star_draft"}
                    if kind == "collect"
                    else {
                        "search_stars",
                        "get_star_details",
                        "get_user_preferences",
                        "generate_quest_proposal",
                    }
                )
                require(expected_nodes <= nodes and expected_tools <= tools, kind + "_workflow_events")
                return body, stage

            def approve(run, stage, id_key, expected, kind):
                endpoint = f"/api/agent/runs/{run['run_id']}/decision"
                # 这是隔离测试程序明确发出的模拟批准，不是用户本人批准。
                decision = {"approved": True, "index": 0}
                first = client.post(endpoint, json=decision)
                require(first.status_code == 200 and first.json().get(id_key), kind + "_approval")
                stage["test_decision"] = {"actor": "isolated_test_simulation", id_key: first.json()[id_key]}
                check_counts(expected, kind + "_approved")
                repeated = client.post(endpoint, json=decision)
                require(
                    repeated.status_code == 200 and repeated.json() == first.json(), kind + "_idempotency"
                )
                check_counts(expected, kind + "_duplicate")
                stage["approval_idempotent"] = True
                stage["after_approval_events"] = client.get("/api/agent/runs/" + run["run_id"]).json()[
                    "events"
                ]
                save()
                return first.json()[id_key]

            collect, stage = generate("collect", {"request_type": "collect", "text": COLLECT_TEXT})
            draft = DraftResult.model_validate(collect["state"]["draft"]).draft
            require(
                draft.original_text == COLLECT_TEXT
                and draft.source_type == "paste"
                and draft.source_reference is None,
                "collect_source",
            )
            require(
                all(
                    getattr(draft, name) is None
                    for name in ("interest_reason", "estimated_minutes", "estimated_budget", "energy_level")
                ),
                "collect_unknown_fields",
            )
            check_counts((0, 0, 0), "collect_before_approval")
            star_id = approve(collect, stage, "star_id", (1, 0, 0), "collect")
            stage["status"] = "passed"
            # 先执行只读确定性检索，不消耗模型请求。
            found = client.get("/api/search", params={"q": EXPLORE_REQUEST["text"]}).json()
            require({item["star_id"] for item in found} == {star_id}, "offline_retrieval")
            report["offline_retrieval_ids"] = [star_id]
            explore, stage = generate("explore", EXPLORE_REQUEST)
            proposals = ProposalResult.model_validate(
                {
                    "proposals": explore["state"]["proposals"],
                    "questions": explore["state"].get("questions", []),
                }
            ).proposals
            check_counts((1, 0, 0), "explore_before_approval")
            if not proposals:
                stage["status"] = "no_valid_proposal"
                report["status"] = "partial"
                save()
                return
            retrieved = {item["star_id"] for item in explore["state"]["related_stars"]}
            require(retrieved == {star_id} and bool(explore["state"]["validation"]), "explore_retrieved_ids")
            from app.rules import TEXT_STEPS

            for proposal in proposals:
                require(
                    set(proposal.based_on_star_ids) <= retrieved
                    and 1 <= proposal.estimated_minutes <= 10
                    and proposal.estimated_budget == 0
                    and proposal.energy_level == "low"
                    and proposal.steps == TEXT_STEPS,
                    "explore_constraints",
                )
            quest_id = approve(explore, stage, "quest_id", (1, 1, 0), "explore")
            quests = client.get("/api/quests").json()
            require(
                len(quests) == 1
                and quests[0]["id"] == quest_id
                and set(quests[0]["based_on_star_ids"]) == {star_id}
                and quests[0]["reflection"] is None,
                "quest_star_relation",
            )
            stage["status"] = "passed"
            report["status"] = "passed"
            check_counts((1, 1, 0), "final")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-live", action="store_true")
    args = parser.parse_args(argv)
    if not args.allow_live:
        parser.error("需要 --allow-live 明确授权最多两次真实工作流请求")
    cache = ROOT / ".cache"
    require(cache.resolve() == cache, "cache_must_be_local")
    cache.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="qwen-workflow-", dir=cache))
    report = {
        "mode": "live",
        "provider": "bailian",
        "model": "qwen3.8-flash",
        "status": "not_run",
        "max_invokes": 2,
        "max_retries": 0,
        "enable_thinking": False,
        "adapter_requests": 0,
        "public_collect_input": COLLECT_TEXT,
        "public_explore_input": EXPLORE_REQUEST,
        "test_preferences": TEST_PREFERENCES,
        "calls": [],
        "stages": {},
        "counts": {},
    }
    report_path = directory / "report.json"
    config = None
    before_environment = dict(os.environ)
    before_hash = file_hash(ROOT / "wonder.db")
    previous_logging = logging.root.manager.disable
    logging.disable(logging.CRITICAL)

    def save():
        write_report(report_path, report, config)

    try:
        # 仅在显式授权后，通过既有 Settings 运行时读取凭据；不浏览/回显 .env。
        config = Settings(
            mock_mode=False, model_provider="bailian", model_name="qwen3.8-flash", model_max_retries=0
        )
        validate_live_config(config)
        report["max_output_tokens"] = config.model_max_tokens
        report["timeout_seconds"] = config.model_timeout
        run_workflow(config, directory, report, save, adapter_module.ChatOpenAI)
    except CheckFailure as exc:
        report.update(status="failed" if report["calls"] else "not_run", error_type=str(exc))
    except Exception:
        report.update(
            status="failed" if report["calls"] else "not_run", error_type="configuration_or_runner_error"
        )
    finally:
        logging.disable(previous_logging)
        report["environment_restored"] = dict(os.environ) == before_environment
        report["personal_database_hash_before"] = before_hash
        report["personal_database_hash_after"] = file_hash(ROOT / "wonder.db")
        if not report["environment_restored"] or report["personal_database_hash_after"] != before_hash:
            report.update(status="failed", error_type="environment_or_personal_database_changed")
        save()
    print(
        f"status={report['status']}; invokes={len(report['calls'])}; report={report_path.relative_to(ROOT)}"
    )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
