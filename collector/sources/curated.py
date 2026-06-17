"""上海重大活动 · 策展源 —— 人工维护的年度重磅活动清单(带真实日期)。

为什么需要它:
  免费爬虫给不出"未来的重大活动"(WAIC/进博会/大师赛等),还会混入过期、
  纯 B2B、不适合儿童的内容。本源是雷达的"可靠骨架"——少而精、有日期、已筛选。

数据状态(2026-06 联网核实):
  有 start 日期者为已核实;note 含"待官方确认"者为档期估计,以官方为准。
维护方式: 直接编辑下方 EVENTS 列表(每年更新档期即可)。
"""
from __future__ import annotations

from typing import List

from models import Event
from sources.base import BaseSource

# 每条: title/type/start/end/venue/kid/age/featured/url/note/tags
EVENTS = [
    {
        "title": "世界人工智能大会 WAIC 2026", "type": "展会",
        "start": "2026-07-17", "end": "2026-07-20", "venue": "世博展览馆",
        "kid": True, "age": "8岁+", "featured": True, "url": "",
        "note": "AI 科普展区适合大童", "tags": ["AI/科技"],
    },
    {
        "title": "中国国际工业博览会(工博会)2026", "type": "展会",
        "start": "2026-10-12", "end": "2026-10-16", "venue": "国家会展中心(虹桥)",
        "kid": True, "age": "8岁+", "featured": True, "url": "",
        "note": "机器人/智能制造展区", "tags": ["科技/机器人"],
    },
    {
        "title": "第九届中国国际进口博览会(进博会)", "type": "展会",
        "start": "2026-11-05", "end": "2026-11-10", "venue": "国家会展中心(虹桥)",
        "kid": False, "age": "", "featured": True, "url": "https://www.ciie.org/",
        "note": "公众日需预约,以官方为准", "tags": [],
    },
    {
        "title": "上海劳力士大师赛(网球 ATP1000)2026", "type": "体育",
        "start": "2026-10-07", "end": "2026-10-19", "venue": "旗忠森林网球中心",
        "kid": True, "age": "全年龄", "featured": True,
        "url": "https://www.jussevent.com/", "note": "结束日期约,以官方为准",
        "tags": ["网球"],
    },
    {
        "title": "上海马拉松 2026", "type": "体育",
        "start": "2026-12-06", "end": "", "venue": "外滩金牛广场(起点)",
        "kid": True, "age": "全年龄", "featured": True,
        "url": "https://www.shang-ma.com/", "note": "可观赛/亲子跑", "tags": ["跑步"],
    },
    {
        "title": "上海书展", "type": "展会",
        "start": "", "end": "", "venue": "上海展览中心",
        "kid": True, "age": "全年龄", "featured": False, "url": "",
        "note": "档期待官方确认(往年 8 月中旬),非常适合带娃", "tags": ["文化/亲子"],
    },
    {
        "title": "中国上海国际艺术节", "type": "演出",
        "start": "", "end": "", "venue": "多场馆",
        "kid": True, "age": "", "featured": False, "url": "",
        "note": "档期待官方确认(往年 10–11 月),含亲子板块", "tags": ["文化"],
    },
    {
        "title": "上海国际电影节(第28届)", "type": "演出",
        "start": "2026-06-12", "end": "2026-06-21", "venue": "全市影院",
        "kid": True, "age": "全年龄", "featured": True, "url": "https://www.siff.com/",
        "note": "含动画/亲子展映单元", "tags": ["电影"],
    },
    {
        "title": "上海旅游节", "type": "演出",
        "start": "", "end": "", "venue": "全市景点",
        "kid": True, "age": "全年龄", "featured": True, "url": "",
        "note": "档期待官方确认(往年 9 月中–10 月,大量景点半价)", "tags": ["文化/亲子"],
    },
    {
        "title": "上海迪士尼·万圣狂欢", "type": "演出",
        "start": "", "end": "", "venue": "上海迪士尼度假区",
        "kid": True, "age": "全年龄", "featured": True,
        "url": "https://www.shanghaidisneyresort.com/",
        "note": "档期待官方确认(往年 10 月中–11 月初周末)", "tags": ["乐园/亲子"],
    },
    {
        "title": "上海马戏城 杂技/马戏 驻场秀", "type": "演出",
        "start": "", "end": "", "venue": "上海马戏城",
        "kid": True, "age": "全年龄", "featured": False, "url": "",
        "note": "常年驻演(周末有场),猫眼/大麦购票", "tags": ["马戏"],
    },
    {
        "title": "上海儿童艺术剧场 亲子剧目", "type": "演出",
        "start": "", "end": "", "venue": "上海儿童艺术剧场(梅陇)",
        "kid": True, "age": "全年龄", "featured": False, "url": "",
        "note": "常年亲子剧/木偶/音乐会,排期见官网/猫眼", "tags": ["剧场/亲子"],
    },
    {
        "title": "上海天文馆", "type": "展会",
        "start": "", "end": "", "venue": "上海天文馆(临港)",
        "kid": True, "age": "全年龄", "featured": False, "url": "",
        "note": "常年开放,需官网预约;亲子科普顶流", "tags": ["科普/亲子"],
    },
    {
        "title": "上海自然博物馆", "type": "展会",
        "start": "", "end": "", "venue": "自然博物馆(静安雕塑公园)",
        "kid": True, "age": "全年龄", "featured": False, "url": "",
        "note": "常年开放+当期特展,需预约;亲子科普", "tags": ["科普/亲子"],
    },
    {
        "title": "上海科技馆", "type": "展会",
        "start": "", "end": "", "venue": "上海科技馆(浦东)",
        "kid": True, "age": "全年龄", "featured": False, "url": "",
        "note": "常年开放,亲子科普", "tags": ["科普/亲子"],
    },
    {
        "title": "上海玻璃博物馆 儿童艺术馆", "type": "展会",
        "start": "", "end": "", "venue": "玻璃博物馆(宝山)",
        "kid": True, "age": "全年龄", "featured": False, "url": "",
        "note": "玻璃主题亲子体验,常年开放", "tags": ["科普/亲子"],
    },
    {
        "title": "上海木偶剧团 亲子木偶剧", "type": "演出",
        "start": "", "end": "", "venue": "多剧场",
        "kid": True, "age": "全年龄", "featured": False, "url": "",
        "note": "常年亲子木偶/皮影,排期见官网/猫眼", "tags": ["剧场/亲子"],
    },
    {
        "title": "世界移动通信大会 MWC上海 2026", "type": "展会",
        "start": "2026-06-24", "end": "2026-06-26", "venue": "上海新国际博览中心",
        "kid": False, "age": "", "featured": True,
        "url": "https://www.mwcshanghai.cn/", "note": "移动AI/6G/卫星通信",
        "tags": ["科技/通信"],
    },
    {
        "title": "ChinaJoy 2026(中国国际数码互动娱乐展)", "type": "展会",
        "start": "2026-07-31", "end": "2026-08-03", "venue": "上海新国际博览中心",
        "kid": True, "age": "青少年", "featured": True,
        "url": "https://www.chinajoy.net/", "note": "游戏/ACG,适合大童青少年",
        "tags": ["游戏/ACG"],
    },
    {
        "title": "华为全连接大会 HUAWEI CONNECT 2026", "type": "展会",
        "start": "2026-09-17", "end": "2026-09-19", "venue": "世博展览馆",
        "kid": False, "age": "", "featured": True,
        "url": "https://www.huawei.com/cn/events/huaweiconnect",
        "note": "档期以华为官方为准(往年9月中旬)", "tags": ["科技/AI"],
    },
]


# 固定场馆(常年滚动排期,无单一日期)—— 命中即归"固定场馆",其余策展归"年度固定"
_VENUE_KW = ["天文馆", "自然博物馆", "科技馆", "玻璃博物馆", "马戏城",
             "儿童艺术剧场", "木偶剧团", "音乐厅", "大剧院", "东方艺术中心"]


def _kind(title: str) -> str:
    return "固定场馆" if any(k in title for k in _VENUE_KW) else "年度固定"


class CuratedSource(BaseSource):
    name = "curated"
    compliance = "high"  # 人工策展,无抓取

    def fetch(self) -> List[Event]:
        events = [
            Event(
                title=e["title"], type=e["type"], source=self.name,
                official_url=e["url"], venue=e["venue"],
                start_date=e["start"], end_date=e["end"],
                kid_friendly=e["kid"], age_range=e["age"],
                featured=e["featured"], note=e["note"], tags=list(e["tags"]),
                kind=_kind(e["title"]), raw_text=e["title"],
            )
            for e in EVENTS
        ]
        print(f"[curated] 重大活动 {len(events)} 条")
        return events
