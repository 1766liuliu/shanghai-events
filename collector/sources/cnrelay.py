"""境内中继源 —— 读取由中国境内节点(阿里云函数计算 FC)抓取并提交回仓库的
data/cn_events.json,转成标准 Event 走现有清洗/去重/交叉引用管线。

为什么需要它:GitHub Actions 跑在境外,儿艺剧场/木偶剧团/大河票务/文化云等
境内站点境外不可达。中继节点在上海定时抓取 → 输出 cn_events.json → 用 token
提交回本仓库 → 本源把它读进来。**GitHub Actions 全程不碰中国网络。**

约定(中继侧只需输出"原始结构",清洗交给本管线):
  · cn_events.json 是一个 JSON 数组,每项是一个对象;
  · 字段名对齐 models.Event(title/type/source/official_url/venue/
    start_date/end_date/...);未知字段(如 _id / programs)自动忽略;
  · 演出类(儿艺/木偶等)给对 venue 名,会自动交叉引用进对应固定场馆卡片。
文件不存在 = 中继尚未部署 → 静默返回空,不报错。
"""
from __future__ import annotations

import dataclasses
import json
import os
from typing import List

from models import Event
from sources.base import BaseSource

CN_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "cn_events.json")
_VALID_FIELDS = {f.name for f in dataclasses.fields(Event)}


class CnRelaySource(BaseSource):
    name = "cnrelay"
    compliance = "mid"

    def fetch(self) -> List[Event]:
        path = os.path.abspath(CN_PATH)
        if not os.path.exists(path):
            print("[cnrelay] data/cn_events.json 不存在(中继未部署),跳过")
            return []
        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
        except Exception as e:  # noqa: BLE001
            print(f"[cnrelay] 读取失败: {e}")
            return []
        if not isinstance(raw, list):
            print("[cnrelay] 格式异常: 顶层应为数组,跳过")
            return []

        events: List[Event] = []
        for item in raw:
            if not isinstance(item, dict) or not item.get("title"):
                continue
            kw = {k: v for k, v in item.items() if k in _VALID_FIELDS}
            kw.setdefault("source", "cnrelay")  # 中继若未标来源,统一兜底
            try:
                events.append(Event(**kw))
            except Exception as e:  # noqa: BLE001
                print(f"[cnrelay] 跳过一条(构造失败 {e}): {str(item)[:60]}")
        print(f"[cnrelay] 从 cn_events.json 读入 {len(events)} 条")
        return events
