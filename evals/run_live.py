"""显式授权的有限 Live collect 检查；不导入数据库或运行审批。"""

import argparse
import json
import re
import sys
from pathlib import Path
from time import perf_counter
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.config import Settings
from app.model_adapter import ModelAdapter, ModelFailure
from app.schemas import AgentRequest


def validate_live_config(config: Settings) -> None:
    """只做本地格式检查，不联网验证 Key、Host、权限或额度。错误不包含配置值。"""
    key = config.model_api_key.strip()
    if not key or key.lower() in {"test-placeholder", "your-api-key", "sk-xxx", "changeme"}:
        raise ValueError("MODEL_API_KEY 必须在本地配置有效密钥；不会使用 Mock 替代")
    if config.mock_mode or config.effective_mock:
        raise ValueError("必须显式配置 MOCK_MODE=false")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,127}", config.model_name):
        raise ValueError("MODEL_NAME 必须是明确的模型标识")
    try:
        url = urlsplit(config.model_api_base_url)
        valid = (
            url.scheme == "https"
            and url.hostname
            and not url.username
            and not url.password
            and not url.query
            and not url.fragment
            and url.port in {None, 443}
            and url.path.rstrip("/").endswith("/v1")
        )
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("MODEL_API_BASE_URL 需要不含凭据、查询串的 HTTPS /v1 地址")
    if config.model_provider == "bailian":
        if config.model_name != "qwen3.8-flash":
            raise ValueError("本阶段百炼 Live 入口仅准备 qwen3.8-flash，不自动更换模型")
        if not (
            re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.cn-beijing\.maas\.aliyuncs\.com", url.hostname)
            and url.path.rstrip("/") == "/compatible-mode/v1"
            and not url.hostname.startswith(("example.", "your-workspace.", "test-workspace."))
        ):
            raise ValueError("百炼需要北京业务空间专属 Host 和 /compatible-mode/v1；请替换示例 Host")
    elif config.model_name == "qwen3.8-flash":
        raise ValueError("本阶段 Qwen Live 入口需要 MODEL_PROVIDER=bailian")
    if config.model_max_retries != 0:
        raise ValueError("有限 Live 检查需要 MODEL_MAX_RETRIES=0，避免 SDK 自动重试增加请求")


def positive_count(value: str) -> int:
    count = int(value)
    if count < 1:
        raise argparse.ArgumentTypeError("案例数必须至少为 1")
    return count


def run_cases(config: Settings, cases: list[dict], max_cases: int) -> dict:
    """仅供已完成授权/预检的 main 调用；失败立即停止，不扩案例或降级模型。"""
    model = ModelAdapter(config)
    results = []
    for case in cases[:max_cases]:
        start = perf_counter()
        item = {"case_id": case["id"], "request_type": "collect"}
        try:
            draft = model.draft(AgentRequest(request_type="collect", text=case["text"]))
            item.update(status="schema_valid", result=draft.model_dump(mode="json"))
        except ModelFailure as exc:
            item.update(status="failed", error_type=exc.kind)
        except Exception:
            # 不输出异常字符串/堆栈，以免服务响应包含 Key 或 Authorization。
            item.update(status="failed", error_type="runner_error")
        item["usage"] = model.last_usage
        item["elapsed_ms"] = round((perf_counter() - start) * 1000)
        results.append(item)
        if item["status"] == "failed":
            break
    return {
        "mode": "live",
        "provider": config.model_provider,
        "model": config.model_name,
        "max_cases": max_cases,
        "executed_cases": len(results),
        "max_retries": config.model_max_retries,
        "max_output_tokens": config.model_max_tokens,
        "enable_thinking": False if config.model_provider == "bailian" else None,
        "prompt_version": "v1",
        "workflow_version": "v1",
        "results": results,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-live", action="store_true", help="授权产生真实模型请求及可能的 Token 消耗")
    parser.add_argument("--max-cases", type=positive_count, default=1, help="最多 collect 案例数（默认 1）")
    args = parser.parse_args(argv)
    if not args.allow_live:
        parser.error("需要 --allow-live 明确启用真实模型")
    try:
        config = Settings()
    except Exception:
        parser.error("本地模型配置无法解析；请检查配置类型，不要粘贴密钥或完整配置到对话")
    try:
        validate_live_config(config)
    except ValueError as exc:
        parser.error(str(exc))
    root = Path(__file__).resolve().parents[1]
    cases = json.loads((root / "evals/cases.json").read_text(encoding="utf-8"))["extraction"]
    report = run_cases(config, cases, args.max_cases)
    output = root / ".cache/live-eval.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("结果文件：.cache/live-eval.json（仅固定公开案例，不写数据库）")
    return int(not report["results"] or any(item["status"] == "failed" for item in report["results"]))


if __name__ == "__main__":
    raise SystemExit(main())
