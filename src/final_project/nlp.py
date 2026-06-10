import calendar
import re
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

_MONTH_MAP: dict[str, int] = {
    "january": 1,   "jan": 1,
    "february": 2,  "feb": 2,
    "march": 3,     "mar": 3,
    "april": 4,     "apr": 4,
    "may": 5,
    "june": 6,      "jun": 6,
    "july": 7,      "jul": 7,
    "august": 8,    "aug": 8,
    "september": 9, "sep": 9,  "sept": 9,
    "october": 10,  "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

_MONTH_PAT = (
    r"(?:january|february|march|april|may|june|july|august"
    r"|september|october|november|december"
    r"|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)"
)

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


def _day_of_next_month(today: date, day: int) -> date:
    first = _first_day_of_next_month(today)
    return date(first.year, first.month, day)


def _day_of_month(today: date, day: int) -> date:
    """Return the Nth of current month if N >= today, else fall back to next month."""
    last = calendar.monthrange(today.year, today.month)[1]
    if day <= last and day >= today.day:
        return date(today.year, today.month, day)
    return _day_of_next_month(today, day)


def _resolve_month_day(today: date, month: int, day: int) -> date | None:
    """Return month/day this year, or next year if that date is already past."""
    try:
        candidate = date(today.year, month, day)
    except ValueError:
        return None
    if candidate < today:
        candidate = date(today.year + 1, month, day)
    return candidate


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

    # month name + day  →  "june 14" / "june 14th" / "jun 14th"
    m = re.fullmatch(rf"({_MONTH_PAT}) (?:the )?(\d{{1,2}})(?:st|nd|rd|th)?", s)
    if m:
        result = _resolve_month_day(today, _MONTH_MAP[m.group(1)], int(m.group(2)))
        if result is not None:
            return result

    # day + month name  →  "14 june" / "14th june" / "14th of june"
    m = re.fullmatch(rf"(\d{{1,2}})(?:st|nd|rd|th)? (?:of )?({_MONTH_PAT})", s)
    if m:
        result = _resolve_month_day(today, _MONTH_MAP[m.group(2)], int(m.group(1)))
        if result is not None:
            return result

    # next month + ordinal  →  "next month 14th" / "next month the 14th"
    m = re.fullmatch(r"next month (?:the )?(\d{1,2})(?:st|nd|rd|th)", s)
    if m:
        return _day_of_next_month(today, int(m.group(1)))

    # ordinal + of next month  →  "14th of next month" / "on the 14th of next month"
    m = re.fullmatch(r"(?:on )?(?:the )?(\d{1,2})(?:st|nd|rd|th) of next month", s)
    if m:
        return _day_of_next_month(today, int(m.group(1)))

    # bare ordinal  →  "14th" / "the 14th" / "on the 14th"
    # current month when day >= today, otherwise next month
    m = re.fullmatch(r"(?:on )?(?:the )?(\d{1,2})(?:st|nd|rd|th)", s)
    if m:
        return _day_of_month(today, int(m.group(1)))

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
    # "next month Nth" must come before bare "next month"
    r"\bnext month (?:the )?\d{1,2}(?:st|nd|rd|th)\b",
    r"\bon (?:the )?\d{1,2}(?:st|nd|rd|th) of next month\b",
    r"\b(?:the )?\d{1,2}(?:st|nd|rd|th) of next month\b",
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
    # named month + day — before bare ordinals so "june 14th" isn't split on "14th"
    rf"\b{_MONTH_PAT} (?:the )?\d{{1,2}}(?:st|nd|rd|th)?\b",
    rf"\b\d{{1,2}}(?:st|nd|rd|th)? (?:of )?{_MONTH_PAT}\b",
    # ordinal day — "on the 14th" before bare "14th" to match longer form first
    r"\bon (?:the )?\d{1,2}(?:st|nd|rd|th)\b",
    r"\bthe \d{1,2}(?:st|nd|rd|th)\b",
    r"\b\d{1,2}(?:st|nd|rd|th)\b",
    # bare weekday last (most ambiguous)
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
