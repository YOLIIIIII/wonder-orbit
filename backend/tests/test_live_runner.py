"""Live 入口的离线拒绝/限额测试；绝不启动真实 Live 命令。"""

import importlib.util
import json
import socket
from pathlib import Path

import pytest

from app.config import Settings
from app.model_adapter import ModelFailure
from app.schemas import DraftResult, StarInput

spec = importlib.util.spec_from_file_location(
    "live_runner", Path(__file__).resolve().parents[2] / "evals/run_live.py"
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def config(**changes):
    # 仅内存占位，不是用户 Key 或真实业务空间。
    values = dict(
        _env_file=None,
        mock_mode=False,
        model_provider="bailian",
        model_name="qwen3.8-flash",
        model_api_key="offline-only-placeholder",
        model_max_retries=0,
        model_api_base_url="https://offline-fixture.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    )
    return Settings(**(values | changes))


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def denied(*args, **kwargs):
        pytest.fail("入口单元测试禁止网络")

    monkeypatch.setattr(socket, "getaddrinfo", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)


@pytest.mark.parametrize(
    "changes",
    [
        {"model_api_key": ""},
        {"model_api_key": "  "},
        {"model_api_key": "your-api-key"},
        {"mock_mode": True},
        {"model_name": ""},
        {"model_name": "qwen-expensive"},
        {"model_provider": "openai-compatible"},
        {"model_max_retries": 1},
        {"model_api_base_url": "http://offline-fixture.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"},
        {"model_api_base_url": "https://offline-fixture.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"},
        {"model_api_base_url": "https://example.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"},
        {"model_api_base_url": "https://offline-fixture.cn-beijing.maas.aliyuncs.com/v1"},
        {
            "model_api_base_url": "https://offline-fixture.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions"
        },
        {"model_api_base_url": "https://user:password@example.com/v1"},
        {"model_api_base_url": "https://example.com/v1?key=private"},
        {"model_api_base_url": "https://example.com/v1#private"},
        {"model_api_base_url": "https://example.com:bad/v1"},
    ],
)
def test_preflight_rejects_before_adapter(monkeypatch, capsys, changes):
    monkeypatch.setattr(runner, "Settings", lambda: config(**changes))

    def denied(*args, **kwargs):
        pytest.fail("预检失败后不得构造模型")

    monkeypatch.setattr(runner, "ModelAdapter", denied)
    with pytest.raises(SystemExit) as exc:
        runner.main(["--allow-live", "--max-cases", "1"])
    assert exc.value.code == 2
    error = capsys.readouterr().err
    assert "offline-only-placeholder" not in error
    assert "password" not in error
    assert "key=private" not in error


def test_preflight_accepts_format_only():
    runner.validate_live_config(config())
    runner.validate_live_config(
        config(
            model_provider="openai-compatible",
            model_name="gpt-4o-mini",
            model_api_base_url="https://api.openai.com/v1",
        )
    )


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--max-cases", "1"],
        ["--allow-live", "--max-cases", "0"],
        ["--allow-live", "--max-cases", "-1"],
        ["--allow-live", "--max-cases", "invalid"],
    ],
)
def test_authorization_and_count_before_settings(monkeypatch, argv):
    def denied():
        pytest.fail("无授权/非法数量不应读取 Settings")

    monkeypatch.setattr(runner, "Settings", denied)
    with pytest.raises(SystemExit) as exc:
        runner.main(argv)
    assert exc.value.code == 2


@pytest.mark.parametrize(
    "failure,limit,expected,exit_code",
    [
        (False, None, 1, 0),
        (False, 2, 2, 0),
        (False, 100, 3, 0),
        (True, 3, 1, 1),
    ],
)
def test_main_bounded_public_cases_and_failure_stop(
    monkeypatch, tmp_path, failure, limit, expected, exit_code
):
    root = tmp_path
    (root / "evals").mkdir()
    cases = [{"id": f"public-{i}", "text": "公开测试海洋"} for i in range(3)]
    (root / "evals/cases.json").write_text(json.dumps({"extraction": cases}), encoding="utf-8")
    monkeypatch.setattr(runner, "__file__", str(root / "evals/run_live.py"))
    monkeypatch.setattr(runner, "Settings", config)
    calls = []

    class FakeAdapter:
        last_usage = None

        def __init__(self, config):
            assert config.model_max_retries == 0

        def draft(self, request):
            calls.append(request)
            assert request.request_type == "collect"
            if failure:
                raise ModelFailure("rate_limit")
            self.last_usage = {"input_tokens": 11, "output_tokens": 7, "total_tokens": 18}
            return DraftResult(
                draft=StarInput(title="海洋", original_text=request.text), missing_fields=[], questions=[]
            )

    monkeypatch.setattr(runner, "ModelAdapter", FakeAdapter)
    args = ["--allow-live"] + ([] if limit is None else ["--max-cases", str(limit)])
    assert runner.main(args) == exit_code
    report_text = (root / ".cache/live-eval.json").read_text(encoding="utf-8")
    report = json.loads(report_text)
    assert report["executed_cases"] == len(calls) == expected
    assert "offline-only-placeholder" not in report_text
    assert "offline-fixture.cn-beijing" not in report_text
    assert "Authorization" not in report_text
    assert report["model"] == "qwen3.8-flash"
    assert report["enable_thinking"] is False
    assert report["results"][0]["usage"] == (
        None if failure else {"input_tokens": 11, "output_tokens": 7, "total_tokens": 18}
    )


def test_unexpected_runner_error_is_sanitized(monkeypatch):
    class FakeAdapter:
        last_usage = None

        def __init__(self, config):
            pass

        def draft(self, request):
            raise RuntimeError("Authorization: Bearer secret-not-for-report")

    monkeypatch.setattr(runner, "ModelAdapter", FakeAdapter)
    report = runner.run_cases(config(), [{"id": "public", "text": "公开"}], 1)
    assert report["results"][0]["error_type"] == "runner_error"
    assert "secret-not-for-report" not in json.dumps(report)
