"""可选真实模型评测。默认测试不导入/运行此脚本。"""

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.config import Settings
from app.model_adapter import ModelAdapter, ModelFailure
from app.schemas import AgentRequest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-live", action="store_true")
    args = parser.parse_args()
    if not args.allow_live:
        parser.error("需要 --allow-live 明确启用真实模型")
    config = Settings(mock_mode=False)
    if not config.model_api_key:
        parser.error("MODEL_API_KEY 未配置；真实模型评测不会使用 Mock 替代")
    root = Path(__file__).resolve().parents[1]
    cases = json.loads((root / "evals/cases.json").read_text(encoding="utf-8"))
    model = ModelAdapter(config)
    results = []
    for case in cases["extraction"]:
        start = perf_counter()
        item = {"case_id": case["id"]}
        try:
            draft = model.draft(AgentRequest(request_type="collect", text=case["text"]))
            item.update(status="schema_valid", result=draft.model_dump(mode="json"))
        except ModelFailure as exc:
            item.update(status="failed", error_type=exc.kind)
        item["elapsed_ms"] = round((perf_counter() - start) * 1000)
        results.append(item)
    report = {
        "mode": "live",
        "model": config.model_name,
        "prompt_version": "v1",
        "workflow_version": "v1",
        "results": results,
    }
    output = root / ".cache/live-eval.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"结果文件：{output}")


if __name__ == "__main__":
    main()
