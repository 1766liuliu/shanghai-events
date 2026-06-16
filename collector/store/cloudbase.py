"""微信云开发(CloudBase)存储 —— 通过服务端写入云数据库 events 集合。

凭据从 config.py 读取(见 config.example.py)。首次使用需:
  1. 微信云开发控制台开通环境、建 events / weekly / watch / favorites 集合;
  2. 在腾讯云获取 API 密钥(SecretId / SecretKey),填入 config.py;
  3. pip 安装 tcb 相关 SDK(见 requirements.txt 注释),补全下方 _write。
本文件默认给出"占位实现":未配置则跳过,不影响本地 JSON 调试。
"""
from __future__ import annotations

from typing import List

from models import Event

try:
    from config import CLOUDBASE  # type: ignore
except Exception:  # noqa: BLE001
    CLOUDBASE = {}


def save(events: List[Event]) -> None:
    if not CLOUDBASE.get("env_id"):
        print("[cloudbase] 未配置(config.py 缺 CLOUDBASE.env_id),跳过云写入")
        return
    _write(events)


def _write(events: List[Event]) -> None:
    """TODO: 用 tcb SDK / HTTP API 批量 upsert 到 events 集合。

    建议按 _id 做 upsert(已存在则更新),避免重复。
    """
    print(f"[cloudbase] (待实现)将 upsert {len(events)} 条到环境 "
          f"{CLOUDBASE['env_id']} 的 events 集合")
