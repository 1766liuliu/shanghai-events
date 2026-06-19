"""采集层调度入口。

用法(在 collector/ 目录下运行):
  python main.py            # 跑全部启用源 → 清洗 → 打标 → 存本地 JSON(data/events.json)
  python main.py --cloud    # 同时写入微信云数据库(需 config.py 配置)

新增数据源:
  1. 在 collector/sources/ 下新建 XxxSource(继承 BaseSource,实现 fetch);
  2. 加进下方 ENABLED_SOURCES。
"""
from __future__ import annotations

import sys

from pipeline.classify import classify
from pipeline.clean import clean
from pipeline.freshness import keep_upcoming
from pipeline.links import add_fallback_links
from pipeline.newness import mark_new
from pipeline.region import filter_shanghai
from pipeline.safety import filter_safe
from pipeline.tagging import tag
from sources.bendibao import BendibaoSource
from sources.cnrelay import CnRelaySource
from sources.curated import CuratedSource
from sources.jufair import JufairSource
from sources.jussevent import JussventSource
from sources.maoyan import MaoyanSource
from sources.shcstheatre import ShcstheatreSource
from sources.wenhuayun import WenhuayunSource
from store import cloudbase, html_preview, local_json, site

# 启用的源(策展骨架在前,爬虫作补充)
ENABLED_SOURCES = [
    CuratedSource(),     # ✅ 重大活动策展骨架(WAIC/进博/大师赛…,带真实日期)
    MaoyanSource(),      # ✅ 猫眼演出: 演唱会/剧场/马戏/魔术(带日期/场馆)
    JufairSource(),      # ✅ 聚展: 上海国际展会(带日期+链接)
    ShcstheatreSource(), # ✅ 上海文化广场: 音乐剧/话剧/舞剧排期
    BendibaoSource(),    # ✅ 本地宝: 展会/演出(补充,日期多待核实)
    JussventSource(),    # ✅ 久事体育: 官方赛事动态
    CnRelaySource(),     # ✅ 境内中继: 读 data/cn_events.json(阿里云FC抓取后提交回仓库)
    WenhuayunSource(),   # ⏳ 待抓包对接(亲子内容最多,优先)
]


def run(to_cloud: bool = False) -> None:
    all_events = []
    for src in ENABLED_SOURCES:
        print(f"\n=== 采集源: {src.name} (合规:{src.compliance}) ===")
        try:
            all_events.extend(src.fetch())
        except Exception as e:  # noqa: BLE001
            print(f"[{src.name}] 异常: {e}")

    events = add_fallback_links(
        keep_upcoming(tag(classify(filter_safe(filter_shanghai(clean(all_events))))))
    )
    events = mark_new(events)   # 标记首次出现日期 → 供"最新"分类
    local_json.save(events)
    html_preview.save(events)   # 本地自包含版(双击/发文件)
    site.save(events)           # 在线托管版(site/,GitHub Pages 用)
    if to_cloud:
        cloudbase.save(events)
    print(f"\n完成: 共 {len(events)} 条活动。")


if __name__ == "__main__":
    run(to_cloud="--cloud" in sys.argv)
