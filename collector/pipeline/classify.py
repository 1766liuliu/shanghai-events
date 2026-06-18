"""活动分级 —— 受众(公众/B2B) + 儿童不宜标记 + 主题黑名单。

· 受众: 爬虫里的"行业专业展"(机床/半导体/物流…)标 audience="B2B",
  前端归入单独的"🏢 行业展"选项卡折叠(策展条目不动,仍在年度大展)。
· 儿童不宜: 深夜场/livehouse/酒吧/惊悚/医美等标 kid_unfit=True,前端"亲子"筛选时隐藏。
· 主题黑名单: 命中即丢弃(THEME_BLOCK 默认空,按用户喜好填,清单可随时改)。
三份关键词清单都在本文件,随时增删。
"""
from __future__ import annotations

from typing import List

from models import Event

# 行业 / B2B 专业展(只对 type==展会 的爬虫条目判定;命中→归"行业展"折叠区)
B2B_KW = [
    "机床", "数控", "染料", "涂料", "油墨", "半导体", "集成电路", "晶圆",
    "泵", "阀门", "管材", "管件", "铸造", "压铸", "锻造", "线缆", "电线", "电缆",
    "物流", "供应链", "仓储", "自动化", "工业", "橡塑", "塑料", "橡胶", "紧固件",
    "粉体", "增材", "模具", "轴承", "液压", "气动", "传感", "仪器仪表", "仪表",
    "焊接", "钣金", "表面处理", "润滑", "齿轮", "密封", "五金", "纺织机械",
    "印刷", "包装机械", "化工", "冶金", "光伏", "氢能", "水处理", "暖通", "制冷",
    "劳保", "安防", "消防", "建材", "幕墙", "门窗", "电力", "船舶", "海工",
    "无人机", "激光", "电子元器件", "PCB", "锂电", "电池技术", "汽配", "轴",
]

# 儿童不宜(不禁止,但"亲子"筛选时隐藏)—— 保守取高确信关键词
KID_UNFIT_KW = [
    "深夜", "午夜", "livehouse", "live house", "酒吧", "夜店", "电音", "蹦迪",
    "威士忌", "调酒", "鸡尾酒", "雪茄", "脱口秀", "惊悚", "恐怖", "鬼屋",
    "医美", "整形", "微醺", "清吧", "酒馆",
]

# 主题黑名单(命中即丢弃)—— 用户指定。注意保留"酒展"(葡萄酒/烈酒博览),
# 只删夜生活类(调酒/夜店/酒吧/livehouse),不要用宽泛的"酒"字。
THEME_BLOCK: List[str] = [
    # 婚庆
    "婚博", "婚纱",
    # 美妆美容
    "美博", "美妆", "美容",
    # 医疗医美
    "医疗器械", "医美", "整形",
    # 夜生活(保留酒展,只删这些)
    "调酒", "鸡尾酒", "夜店", "livehouse", "live house", "酒吧", "清吧", "酒馆", "蹦迪",
]


def classify(events: List[Event]) -> List[Event]:
    out: List[Event] = []
    n_b2b = n_unfit = n_block = 0
    for e in events:
        text = f"{e.title} {e.raw_text} {' '.join(e.tags)}"
        if THEME_BLOCK and any(k in text for k in THEME_BLOCK):
            n_block += 1
            continue
        if e.source != "curated" and e.type == "展会" and any(k in e.title for k in B2B_KW):
            e.audience = "B2B"
            n_b2b += 1
        if any(k in text for k in KID_UNFIT_KW):
            e.kid_unfit = True
            n_unfit += 1
        out.append(e)
    print(f"[classify] 行业展(B2B) {n_b2b} | 儿童不宜 {n_unfit} | 主题黑名单丢弃 {n_block}")
    return out
