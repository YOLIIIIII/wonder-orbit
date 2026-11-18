"""Read-only historical artifact integrity; never imports a sampler or app settings."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify(root, manifest):
    checked = []
    for name, expected in manifest["files"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("path_outside_project")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("historical_artifact_changed: " + name)
        checked.append(name)
    return checked


if __name__ == "__main__":
    manifest = json.loads((ROOT / "evals/knowledge_g_history_manifest.json").read_text(encoding="utf8"))
    print(json.dumps({"verified_files": verify(ROOT, manifest)}, indent=2))
