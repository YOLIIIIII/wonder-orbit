"""真实 LangChain + SDK 内存传输测试；禁止 DNS/HTTP 建连，仅允本机事件循环自唤醒。"""

import json
import socket
from types import SimpleNamespace

import httpx2
import pytest
from langchain_openai import ChatOpenAI

from app.config import Settings
from app.model_adapter import ModelAdapter, ModelFailure
from app.schemas import AgentRequest


BASE = "https://test-workspace.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
DRAFT = {"draft": {"title": "海洋", "original_text": "海洋"}, "missing_fields": [], "questions": []}


def config(**changes):
    values = dict(
        _env_file=None,
        mock_mode=False,
        model_provider="bailian",
        model_api_key="test-placeholder",
        model_name="qwen3.8-flash",
        model_api_base_url=BASE,
        model_max_retries=0,
    )
    return Settings(**(values | changes))


def tool(arguments=None, name="create_star_draft", call_id="call-test"):
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(DRAFT if arguments is None else arguments),
        },
    }


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def denied(*args, **kwargs):
        pytest.fail("离线模型测试禁止真实网络")

    monkeypatch.setattr(socket, "getaddrinfo", denied)
    original_connect = socket.socket.connect

    def local_event_loop_only(sock, address):
        # Windows asyncio 用 loopback socketpair 自唤醒；HTTP DNS/建连仍禁止。
        if isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"}:
            return original_connect(sock, address)
        denied()

    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(socket.socket, "connect", local_event_loop_only)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)


@pytest.fixture
def wire(monkeypatch):
    state = SimpleNamespace(
        calls=[],
        message={"role": "assistant", "content": None, "tool_calls": [tool()]},
        usage={"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20},
        status=200,
    )

    def handle(request):
        state.calls.append({"url": str(request.url), "body": json.loads(request.content)})
        # 不记录 request.headers，Authorization 只含测试值也不复制。
        if state.status == "timeout":
            raise httpx2.ReadTimeout("offline timeout", request=request)
        if state.status != 200:
            return httpx2.Response(state.status, json={"error": {"message": "test-provider-error"}})
        response = {
            "id": "offline-completion",
            "object": "chat.completion",
            "created": 0,
            "model": "qwen3.8-flash",
            "choices": [{"index": 0, "message": state.message, "finish_reason": "tool_calls"}],
        }
        if state.usage is not None:
            response["usage"] = state.usage
        return httpx2.Response(200, json=response)

    with httpx2.Client(transport=httpx2.MockTransport(handle), trust_env=False) as client:

        def factory(**kwargs):
            # bind_tools/invoke/SDK 序列化和响应解析均为实际实现。
            return ChatOpenAI(**kwargs, http_client=client)

        monkeypatch.setattr("app.model_adapter.ChatOpenAI", factory)
        yield state


def test_qwen_wire_payload_and_unknowns(wire):
    model = ModelAdapter(config())
    draft = model.draft(AgentRequest(request_type="collect", text="公开海洋输入", source_type="manual"))
    assert len(wire.calls) == 1
    call = wire.calls[0]
    assert call["url"] == BASE + "/chat/completions"
    body = call["body"]
    assert body["model"] == "qwen3.8-flash"
    assert body["enable_thinking"] is False
    assert body["max_completion_tokens"] == 2048
    assert "max_tokens" not in body
    assert "extra_body" not in body  # SDK 将 extra_body 合并到真实 JSON 顶层。
    assert body["tool_choice"] == {"type": "function", "function": {"name": "create_star_draft"}}
    assert [t["function"]["name"] for t in body["tools"]] == ["create_star_draft"]
    assert draft.draft.original_text == "公开海洋输入"
    assert draft.draft.source_type == "manual"
    assert draft.draft.interest_reason is None
    assert draft.draft.estimated_minutes is None
    assert draft.draft.estimated_budget is None
    assert draft.draft.energy_level is None
    assert model.last_usage == {"input_tokens": 12, "output_tokens": 8, "total_tokens": 20}


@pytest.mark.parametrize(
    "provider,name",
    [
        ("openai-compatible", "gpt-4o-mini"),
        ("openai-compatible", "qwen3.8-flash"),
        ("bailian", "another-model"),
    ],
)
def test_provider_parameters_are_isolated(wire, provider, name):
    ModelAdapter(config(model_provider=provider, model_name=name)).draft(
        AgentRequest(request_type="collect", text="海洋")
    )
    assert "enable_thinking" not in wire.calls[0]["body"]


@pytest.mark.parametrize(
    "message",
    [
        {"role": "assistant", "content": json.dumps(DRAFT)},
        {"role": "assistant", "tool_calls": [tool(name="execute_code")]},
        {"role": "assistant", "tool_calls": [tool(), tool(call_id="call-second")]},
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "bad",
                    "type": "function",
                    "function": {"name": "create_star_draft", "arguments": "{broken"},
                }
            ],
        },
        {
            "role": "assistant",
            "tool_calls": [
                tool(),
                {
                    "id": "bad",
                    "type": "function",
                    "function": {"name": "create_star_draft", "arguments": "{broken"},
                },
            ],
        },
    ],
)
def test_reject_missing_wrong_multiple_and_malformed_calls(wire, message):
    wire.message = message
    with pytest.raises(ModelFailure, match="^invalid_tool_call$"):
        ModelAdapter(config()).draft(AgentRequest(request_type="collect", text="海洋"))


@pytest.mark.parametrize(
    "args",
    [
        {"draft": {"title": "缺原文"}},
        DRAFT | {"execute_sql": "denied"},
        DRAFT | {"draft": {"title": "海洋", "original_text": "海洋", "estimated_budget": -1}},
    ],
)
def test_invalid_arguments_fail_pydantic(wire, args):
    wire.message["tool_calls"] = [tool(args)]
    with pytest.raises(ModelFailure, match="^invalid_model_output$"):
        ModelAdapter(config()).draft(AgentRequest(request_type="collect", text="海洋"))


@pytest.mark.parametrize(
    "status,kind", [(429, "rate_limit"), (503, "model_unavailable"), ("timeout", "timeout")]
)
def test_sdk_errors_are_classified_without_retry(wire, status, kind):
    wire.status = status
    with pytest.raises(ModelFailure, match=f"^{kind}$"):
        ModelAdapter(config()).draft(AgentRequest(request_type="collect", text="海洋"))
    assert len(wire.calls) == 1


def test_usage_absent_is_not_estimated_or_reused(wire):
    model = ModelAdapter(config())
    request = AgentRequest(request_type="collect", text="海洋")
    model.draft(request)
    wire.usage = None
    model.draft(request)
    assert model.last_usage is None


def test_invalid_output_never_persists_and_success_requires_approval(wire, client, monkeypatch):
    monkeypatch.setattr("app.main.adapter", lambda: ModelAdapter(config()))
    wire.message["tool_calls"] = [tool(DRAFT | {"draft": {"title": "bad"}})]
    failed = client.post("/api/agent/runs", json={"request_type": "collect", "text": "海洋"})
    assert failed.status_code == 502
    assert client.get("/api/stars").json() == []
    assert client.get("/api/quests").json() == []
    wire.message["tool_calls"] = [tool()]
    run = client.post("/api/agent/runs", json={"request_type": "collect", "text": "海洋"}).json()
    assert run["status"] == "awaiting_decision"
    assert client.get("/api/stars").json() == []
    endpoint = f"/api/agent/runs/{run['run_id']}/decision"
    assert client.post(endpoint, json={"approved": True}).status_code == 200
    assert client.post(endpoint, json={"approved": True}).status_code == 200
    assert len(client.get("/api/stars").json()) == 1
    assert client.get("/api/quests").json() == []


def test_default_mock_does_not_construct_model(monkeypatch):
    def denied(**kwargs):
        pytest.fail("Mock 不应构造 ChatOpenAI")

    monkeypatch.setattr("app.model_adapter.ChatOpenAI", denied)
    model = ModelAdapter(Settings(_env_file=None, model_api_key="", mock_mode=True))
    result = model.draft(AgentRequest(request_type="collect", text="海洋"))
    assert result.draft.tags == ["海洋"]
    assert result.draft.estimated_budget is None


def test_explore_keeps_its_own_forced_tool(wire):
    from app.schemas import Preferences

    wire.message["tool_calls"] = [
        tool({"proposals": [], "questions": ["请补充"]}, name="generate_quest_proposal")
    ]
    result = ModelAdapter(config()).proposals(
        AgentRequest(request_type="explore", text="海洋"),
        [{"star_id": "fixture-real-id", "title": "海洋", "match_basis": ["海洋"]}],
        Preferences(),
    )
    assert result.proposals == []
    assert wire.calls[0]["body"]["tool_choice"] == {
        "type": "function",
        "function": {"name": "generate_quest_proposal"},
    }


def test_source_and_inferred_reason_are_not_model_facts(wire):
    wire.message["tool_calls"] = [
        tool(
            DRAFT
            | {
                "draft": DRAFT["draft"]
                | {
                    "interest_reason": "模型猜测的动机",
                    "source_type": "link",
                    "source_reference": "https://example.com/invented",
                }
            }
        )
    ]
    draft = ModelAdapter(config()).draft(AgentRequest(request_type="collect", text="海洋"))
    assert draft.draft.interest_reason is None
    assert draft.draft.source_type == "paste"
    assert draft.draft.source_reference is None
