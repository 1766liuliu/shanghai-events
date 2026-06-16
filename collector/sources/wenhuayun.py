"""文化上海云采集器 —— 接入位(待抓包对接)。

文化上海云是移动优先的 SPA,数据走内部 JSON 接口,无公开 API 文档。
亲子内容最多、合规等级高,优先级最高,但需在国内网络抓包拿到接口。

对接步骤(在国内浏览器完成):
  1. 打开文化云网站 / H5,进入"演出 / 展览 / 亲子"列表;
  2. 开发者工具 → Network → XHR,翻页时观察返回 JSON 的请求;
  3. 记录请求 URL、查询参数(分类 / 分页 / 城市)、必要请求头 / 签名;
  4. 把 URL 和参数填到下方 API_URL / PARAMS,补全 _parse_item 字段映射;
  5. 运行 main.py 验证。
"""
from __future__ import annotations

from typing import List

import requests

from models import Event
from sources.base import BaseSource

API_URL = ""   # TODO: 抓包后填入活动列表接口
PARAMS: dict = {}  # TODO: 分类 / 分页参数
HEADERS: dict = {}  # TODO: 若接口需要特定请求头 / token


class WenhuayunSource(BaseSource):
    name = "wenhuayun"
    compliance = "high"

    def fetch(self) -> List[Event]:
        if not API_URL:
            print("[wenhuayun] 未配置接口(见文件头部对接指引),跳过")
            return []
        try:
            resp = requests.get(
                API_URL, params=PARAMS, headers=HEADERS, timeout=self.timeout
            )
            payload = resp.json()
        except Exception as e:  # noqa: BLE001
            print(f"[wenhuayun] 抓取失败: {e}")
            return []
        # TODO: 根据实际返回结构调整取列表的路径
        items = payload.get("data", []) if isinstance(payload, dict) else []
        return [self._parse_item(it) for it in items if self._parse_item(it)]

    def _parse_item(self, it: dict) -> Event | None:
        # TODO: 把文化云字段映射到 Event(下面是占位示例)
        title = it.get("name") or it.get("title")
        if not title:
            return None
        return Event(
            title=title,
            type=it.get("category", "演出"),
            source=self.name,
            official_url=it.get("url", ""),
            venue=it.get("venue", ""),
            start_date=it.get("startDate", ""),
            cover=it.get("cover", ""),
            raw_text=str(it),
        )
