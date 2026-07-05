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
  · 数据源:人工策展(curated_beijing)+ 已验证可用的自动抓取源
    (bendibao_beijing / laoshechaguan);猫眼(maoyan)已实测排除,
    理由见下方 ENABLED_SOURCES_BJ 注释。

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
from sources.bendibao_beijing import BendibaoBeijingSource
from sources.curated_beijing import CuratedBeijingSource
from sources.laoshechaguan import LaosheChaguanSource
from sources.showstart_beijing import ShowstartBeijingSource
from store import site

LASTGOOD_BJ = os.path.join(os.path.dirname(__file__), "..", "data", "lastgood_beijing.json")
SEEN_BJ = os.path.join(os.path.dirname(__file__), "..", "data", "seen_beijing.json")

# 启用的源。
# 猫眼(maoyan)已排除:实测 cityId cookie 对 show.maoyan.com 无效,永远返回
# "上海城市默认页"(兰心大戏院/天蟾逸夫舞台等不含"上海"字样,filter_beijing 接不住,
# 会把上海内容错判成北京)。也试过 /beijing、bj.maoyan.com 等路径,均 404/不可达。
# 结论:猫眼北京化不可行,放弃,不接入。
ENABLED_SOURCES_BJ = [
    CuratedBeijingSource(),    # ✅ 北京重大场馆/年度活动策展骨架(已联网核实真实信息)
    BendibaoBeijingSource(),   # ✅ 北京本地宝:演出+展会时间表(bj.bendibao.com,已实测结构,城市天然隔离)
    LaosheChaguanSource(),     # ✅ 老舍茶馆官方排期(i.laoshechaguan.cn,SSR,已实测结构)
    ShowstartBeijingSource(),  # ✅ 秀动网北京演出(破匿名签名接口直取JSON,近期演唱会/livehouse主力源)
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
