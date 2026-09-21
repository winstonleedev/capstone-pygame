from __future__ import annotations

import importlib.util
from pathlib import Path


def main() -> None:
    app_path = Path(__file__).resolve().parents[2] / "app.py"
    if not app_path.exists():
        raise FileNotFoundError("The game entry file app.py was not found.")

    spec = importlib.util.spec_from_file_location("game_app", app_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    module.main()
