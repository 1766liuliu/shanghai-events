"""地域过滤 —— 只保留上海的活动,剔除漏进来的外地展会/巡演站。

规则:标题/场馆里出现"外地城市",且没有任何"上海信号"(上海/上海地标/上海场馆)→ 丢弃。
  · 这样 "深圳食博会""F4…宁波站" 会被剔除;
  · 而 "魔法奇妙夜…外滩…南京路"(南京路是上海地标)会被保留,不误杀。
"""
from __future__ import annotations

from typing import List

from models import Event

# 上海信号(命中任一即视为上海,优先于外地词)
SH_SIGNALS = [
    "上海", "外滩", "浦东", "浦西", "静安", "徐汇", "虹口", "杨浦", "黄浦",
    "闵行", "宝山", "嘉定", "松江", "青浦", "奉贤", "金山", "临港", "虹桥",
    "世博", "陆家嘴", "人民广场", "南京路", "南京东路", "新天地", "豫园",
    "迪士尼", "旗忠", "梅赛德斯", "奔驰文化中心", "东方体育", "虹口足球场",
    "国家会展中心", "新国际博览", "世博展览馆", "上海展览中心",
]

# 外地城市(出现且无上海信号 → 判为外地)
OTHER_CITIES = [
    "北京", "广州", "深圳", "成都", "杭州", "南京", "武汉", "重庆", "宁波",
    "青岛", "天津", "西安", "苏州", "长沙", "郑州", "合肥", "沈阳", "大连",
    "无锡", "东莞", "佛山", "厦门", "济南", "昆明", "哈尔滨", "福州", "南昌",
    "贵阳", "太原", "石家庄", "烟台", "温州", "珠海", "海口", "三亚", "长春",
]


def filter_shanghai(events: List[Event]) -> List[Event]:
    out: List[Event] = []
    dropped = 0
    for e in events:
        text = f"{e.title} {e.venue}"
        if any(s in text for s in SH_SIGNALS):
            out.append(e)
            continue
        if any(c in text for c in OTHER_CITIES):
            dropped += 1
            continue
        out.append(e)  # 没提任何城市 → 默认保留(来自上海源)
    print(f"[region] 剔除外地活动 {dropped} 条,保留 {len(out)} 条")
    return out
