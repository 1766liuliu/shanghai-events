"""北京采集层调度入口(与 collector/main.py 上海版完全独立并行,互不影响)。

用法(在 collector/ 目录下运行):
  python main_beijing.py

设计原则(务必保持,任何一条都不能为图省事共享上海的状态文件):
  · 独立数据文件:data/curated_beijing.toml(不读/不写 curated.toml)
  · 独立地域过滤:pipeline/region_beijing.py(不共享 region.py 状态)
  · 独立质量闸状态:data/lastgood_beijing.json(不与上海 lastgood.json 混用)
  · 独立"最新"去重状态:data/seen_beijing.json(不与上海 seen.json 混用,
    否则"首次启用全部回填为非新"的判定会被上海已有记录带偏)
  · 独立输出:events_beijing.json(不覆盖 events.json;index.html 由上海 main.py 统一生成/更新,
    本入口不重复写,因为页面模板已内置城市切换、city-agnostic)
  · 骨架版:目前只用已联网核实的人工策展数据(curated_beijing);
    未接自动抓取源(踩坑见下方 ENABLED_SOURCES_BJ 注释),后续需同上海历史路径逐个探测北京源。

新增北京数据源:同上海一样,在 collector/sources/ 下新建 XxxSource,加进下方 ENABLED_SOURCES_BJ。
"""
from __future__ import annotations

import os

from quality import gated_fetch
from pipeline.classify import classify
from pipeline.clean import clean
from pipeline.freshness import keep_upcoming
from pipeline.links import add_fallback_links
from pipeline.newness import mark_new
from pipeline.region_beijing import filter_beijing
from pipeline.safety import filter_safe
from pipeline.tagging import tag
from sources.curated_beijing import CuratedBeijingSource
from store import site

LASTGOOD_BJ = os.path.join(os.path.dirname(__file__), "..", "data", "lastgood_beijing.json")
SEEN_BJ = os.path.join(os.path.dirname(__file__), "..", "data", "seen_beijing.json")

# 启用的源(骨架版:只用已联网核实的策展数据,故意不接猫眼)。
# 实测发现 sources.maoyan 抓的其实是"上海城市默认页"——很多上海场馆
# (兰心大戏院/天蟾逸夫舞台/宛平剧院等)不含"上海"字样,filter_beijing 接不住,
# 会把上海内容错判成北京、造成"交叉污染"。在没有北京专属入口(cityId/子域名)
# 前,宁可数据少也不接这个源。后续要扩量,需同上海当年一样逐个探测北京源。
ENABLED_SOURCES_BJ = [
    CuratedBeijingSource(),  # ✅ 北京重大场馆/年度活动策展骨架(已联网核实真实信息)
]


def run() -> None:
    all_events, health = gated_fetch(ENABLED_SOURCES_BJ, lastgood_path=LASTGOOD_BJ)

    events = add_fallback_links(
        keep_upcoming(tag(classify(filter_safe(filter_beijing(clean(all_events))))))
    )
    events = mark_new(events, seen_path=SEEN_BJ)
    site.save(events, health, city="北京")
    print(f"\n完成(北京): 共 {len(events)} 条活动。")


if __name__ == "__main__":
    run()
