from dataclasses import dataclass, field
from enum import StrEnum


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
