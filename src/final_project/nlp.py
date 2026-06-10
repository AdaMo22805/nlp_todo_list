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
