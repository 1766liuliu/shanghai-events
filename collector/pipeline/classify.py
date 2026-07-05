"""活动分级 —— 受众(公众/B2B) + 儿童不宜标记 + 主题黑名单。

· 受众: 爬虫抓的展会**默认 B2B**(归"🏢 行业展"折叠),仅消费类(动漫/童书/车展…)留公众;
  策展条目不动,仍在年度大展。
· 儿童不宜: 深夜场/livehouse/酒吧/惊悚/医美等标 kid_unfit=True,前端"亲子"筛选时隐藏。
· 主题黑名单: 命中即丢弃(THEME_BLOCK 默认空,按用户喜好填,清单可随时改)。
三份关键词清单都在本文件,随时增删。
"""
from __future__ import annotations

from typing import List

from models import Event

# 公众/消费类展会"白名单":爬虫抓的展会**默认都当 B2B 行业展**(归"行业展"折叠),
# 只有标题命中下列消费类关键词的,才算公众展、留在"近期活动"。
# (反向逻辑:行业词列不全,但消费类是有限的;默认 B2B 才不会漏。)
PUBLIC_KW = [
    "动漫", "漫展", "二次元", "游戏", "电竞", "手办", "潮玩", "谷子",
    "童书", "绘本", "玩具", "亲子", "儿童", "母婴", "插画", "cosplay",
    "宠物", "萌宠", "车展", "房车", "花展", "园艺", "盆栽", "多肉",
    "文创", "非遗", "手作", "市集", "集市", "年货", "茶博", "咖啡",
    "珠宝", "文玩", "邮票", "钱币", "模型", "积木",
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
        # 爬虫抓的展会:默认 B2B(行业展),命中消费类白名单才算公众。
        # 人工策展源(curated / curated_beijing…,均以 "curated" 开头)不受此默认影响。
        if (not e.source.startswith("curated") and e.type == "展会"
                and not any(k in e.title for k in PUBLIC_KW)):
            e.audience = "B2B"
            n_b2b += 1
        if any(k in text for k in KID_UNFIT_KW):
            e.kid_unfit = True
            n_unfit += 1
        out.append(e)
    print(f"[classify] 行业展(B2B) {n_b2b} | 儿童不宜 {n_unfit} | 主题黑名单丢弃 {n_block}")
    return out
