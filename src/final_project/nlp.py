import calendar
import re
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

_WEEKDAY_MAP: dict[str, int] = {
    "monday": 0,    "mon": 0,
    "tuesday": 1,   "tue": 1,
    "wednesday": 2, "wed": 2,
    "thursday": 3,  "thu": 3,
    "friday": 4,    "fri": 4,
    "saturday": 5,  "sat": 5,
    "sunday": 6,    "sun": 6,
}


def _parse_weekday(name: str) -> int | None:
    return _WEEKDAY_MAP.get(name.lower().rstrip("."))


def _next_weekday(weekday: int, today: date) -> date:
    """Strictly next occurrence of weekday after today (never today itself)."""
    days = (weekday - today.weekday()) % 7 or 7
    return today + timedelta(days=days)


def _last_day_of_month(d: date) -> date:
    return date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])


def _first_day_of_next_month(d: date) -> date:
    return d.replace(day=1) + relativedelta(months=1)


def _add_unit(d: date, n: int, unit: str) -> date:
    if unit.startswith("day"):
        return d + timedelta(days=n)
    if unit.startswith("week"):
        return d + timedelta(weeks=n)
    return d + relativedelta(months=n)


def parse_date_phrase(phrase: str, today: date | None = None) -> date | None:
    """Parse a natural-language date phrase into a date, or return None on no match.

    Args:
        phrase: Natural-language input, e.g. "tomorrow", "next friday", "in 2 weeks".
        today:  Reference date for relative calculations; defaults to date.today().
    """
    if today is None:
        today = date.today()

    s = phrase.strip().lower()

    # today / tomorrow shorthands
    if s in ("today", "tod"):
        return today
    if s in ("tomorrow", "tmr", "tmrw", "tom"):
        return today + timedelta(days=1)

    # period anchors
    if s in ("end of week", "eow"):
        return _next_weekday(4, today)      # coming Friday
    if s in ("end of month", "eom"):
        return _last_day_of_month(today)
    if s == "next month":
        return _first_day_of_next_month(today)

    # first <weekday> of next month
    m = re.fullmatch(r"first (\w+\.?) of next month", s)
    if m:
        wd = _parse_weekday(m.group(1))
        if wd is not None:
            first_next = _first_day_of_next_month(today)
            return first_next + timedelta(days=(wd - first_next.weekday()) % 7)

    # next <weekday>  →  one full week after the bare result
    m = re.fullmatch(r"next (\w+\.?)", s)
    if m:
        wd = _parse_weekday(m.group(1))
        if wd is not None:
            return _next_weekday(wd, today) + timedelta(days=7)

    # this / upcoming <weekday>  →  same as bare
    m = re.fullmatch(r"(?:this|upcoming) (\w+\.?)", s)
    if m:
        wd = _parse_weekday(m.group(1))
        if wd is not None:
            return _next_weekday(wd, today)

    # in N days/weeks/months
    m = re.fullmatch(r"in (\d+|a) (day|days|week|weeks|month|months)", s)
    if m:
        n = 1 if m.group(1) == "a" else int(m.group(1))
        return _add_unit(today, n, m.group(2))

    # N days/weeks/months from now
    m = re.fullmatch(r"(\d+|a) (day|days|week|weeks|month|months) from now", s)
    if m:
        n = 1 if m.group(1) == "a" else int(m.group(1))
        return _add_unit(today, n, m.group(2))

    # bare weekday name or abbreviation
    wd = _parse_weekday(s)
    if wd is not None:
        return _next_weekday(wd, today)

    return None


# ---------- inline extraction ----------

_WEEKDAY_PAT = r"(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)"

_INLINE_PATTERNS: list[re.Pattern[str]] = [re.compile(p, re.IGNORECASE) for p in [
    # most specific (multi-word) first to avoid partial matches
    rf"\bfirst {_WEEKDAY_PAT} of next month\b",
    r"\bend of week\b",
    r"\bend of month\b",
    r"\bnext month\b",
    rf"\bnext {_WEEKDAY_PAT}\b",
    rf"\b(?:this|upcoming) {_WEEKDAY_PAT}\b",
    r"\bin (?:\d+|a) (?:days?|weeks?|months?)\b",
    r"\b(?:\d+|a) (?:days?|weeks?|months?) from now\b",
    r"\btomorrow\b",
    r"\btmrw\b",
    r"\btmr\b",
    r"\btoday\b",
    r"\beow\b",
    r"\beom\b",
    # bare weekday last (most ambiguous — only match after all multi-word attempts fail)
    rf"\b{_WEEKDAY_PAT}\b",
]]


def extract_date_from_text(
    text: str, today: date | None = None
) -> tuple[str, date | None]:
    """Scan text for an inline date phrase; return (cleaned_text, date) or (text, None).

    The first matching phrase is extracted and removed; surrounding whitespace is
    collapsed.  Returns the original text unchanged when no phrase is found.
    """
    if today is None:
        today = date.today()

    for pattern in _INLINE_PATTERNS:
        m = pattern.search(text)
        if m:
            parsed = parse_date_phrase(m.group(0), today=today)
            if parsed is not None:
                cleaned = (text[: m.start()] + text[m.end() :]).strip()
                cleaned = re.sub(r" {2,}", " ", cleaned)
                return cleaned, parsed

    return text, None
