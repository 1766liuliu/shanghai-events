"""调试存储 —— 写本地 JSON,无需云密钥即可验证全链路。"""
from __future__ import annotations

import json
import os
from typing import List

from models import Event

DEFAULT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "events.json"
)


def save(events: List[Event], path: str = DEFAULT_PATH) -> None:
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = [e.to_dict() for e in events]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[local_json] 已写入 {len(data)} 条 → {path}")
