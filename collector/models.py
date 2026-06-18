"""事件数据模型 —— 采集层与云数据库共用的统一结构。"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class Event:
    title: str                        # 活动名称
    type: str                         # 体育 / 展会 / 演出
    source: str                       # 数据来源标识(如 bendibao)
    official_url: str = ""            # 官方详情 / 购票链接
    venue: str = ""                   # 场馆
    district: str = ""                # 行政区
    start_date: str = ""              # YYYY-MM-DD
    end_date: str = ""                # YYYY-MM-DD
    open_ticket_time: str = ""        # 开票时间(可空)
    price_range: str = ""             # 价格区间文字
    price_min: Optional[int] = None   # 最低价(元),用于筛选
    kid_friendly: bool = False        # 是否亲子适合
    age_range: str = ""               # 适龄(如 "3-8岁")
    tags: list = field(default_factory=list)
    cover: str = ""                   # 封面图 URL
    status: str = "upcoming"          # upcoming / onsale / ended
    featured: bool = False            # 重磅活动(策展标记)
    kind: str = "临时"                # 形态: 年度固定 / 固定场馆 / 临时(决定分区)
    audience: str = "公众"            # 受众: 公众 / B2B(B2B 归"行业展"折叠)
    kid_unfit: bool = False           # 儿童不宜(亲子筛选时隐藏)
    note: str = ""                    # 备注(如"档期待官方确认")
    first_seen: str = ""              # 首次被采集到的日期 YYYY-MM-DD(用于"最新")
    raw_text: str = ""                # 原始文本(便于回溯 / 打标)

    @property
    def event_id(self) -> str:
        """根据来源+标题+开始日期生成稳定去重 ID。"""
        key = f"{self.source}|{self.title}|{self.start_date}"
        return hashlib.md5(key.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict:
        d = asdict(self)
        d["_id"] = self.event_id
        return d
