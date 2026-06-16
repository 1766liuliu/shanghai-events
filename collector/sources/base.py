"""数据源基类 —— 新增一个源 = 继承 BaseSource 并实现 fetch()。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from models import Event


class BaseSource(ABC):
    name: str = "base"           # 源标识(唯一)
    compliance: str = "unknown"  # 合规等级: high / mid / gray
    timeout: int = 15            # 抓取超时(秒)

    @abstractmethod
    def fetch(self) -> List[Event]:
        """抓取并返回 Event 列表(只负责拿数据+粗结构化,不做清洗/打标)。"""
        raise NotImplementedError
