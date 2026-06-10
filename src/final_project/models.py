from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

try:
    from enum import StrEnum
except ImportError:
    class StrEnum(str, Enum):  # type: ignore[no-redef]
        def __str__(self) -> str:
            return self.value


class Priority(StrEnum):
    NEVER = "never"
    LOW = "low"
    MED = "med"
    HIGH = "high"


@dataclass
class Task:
    id: int
    text: str
    due: str | None = None
    priority: Priority = Priority.LOW
    tags: list[str] = field(default_factory=list)
    done: bool = False
    created_at: str = ""
    completed_at: str | None = None
    raw: str = ""
