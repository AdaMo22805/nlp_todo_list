"""Tests for natural-language date phrase parsing.

All tests pin `today` to Wednesday 2026-06-10 for determinism.

Weekday reference from that anchor:
  Thu Jun 11 · Fri Jun 12 · Sat Jun 13 · Sun Jun 14
  Mon Jun 15 · Tue Jun 16 · Wed Jun 17  (next Wed)
  ...next-week Fri Jun 19 · next-week Mon Jun 22 · next-week Wed Jun 24
  Jul 3 = first Friday of July
  Jul 6 = first Monday of July
"""

from datetime import date

import pytest

from final_project.nlp import extract_date_from_text, parse_date_phrase

TODAY = date(2026, 6, 10)  # Wednesday


# ---------- today / tomorrow shorthands ----------

@pytest.mark.parametrize("phrase,expected", [
    ("today",    date(2026, 6, 10)),
    ("tod",      date(2026, 6, 10)),
    ("Today",    date(2026, 6, 10)),
    ("TODAY",    date(2026, 6, 10)),
    ("tomorrow", date(2026, 6, 11)),
    ("Tomorrow", date(2026, 6, 11)),
    ("tmr",      date(2026, 6, 11)),
    ("tmrw",     date(2026, 6, 11)),
    ("tom",      date(2026, 6, 11)),
])
def test_today_tomorrow_shorthands(phrase, expected):
    assert parse_date_phrase(phrase, today=TODAY) == expected


# ---------- bare weekday names ----------

@pytest.mark.parametrize("phrase,expected", [
    # Full names — case insensitive
    ("thursday",  date(2026, 6, 11)),
    ("Thursday",  date(2026, 6, 11)),
    ("THURSDAY",  date(2026, 6, 11)),
    ("friday",    date(2026, 6, 12)),
    ("Friday",    date(2026, 6, 12)),
    ("FRIDAY",    date(2026, 6, 12)),
    ("saturday",  date(2026, 6, 13)),
    ("sunday",    date(2026, 6, 14)),
    ("monday",    date(2026, 6, 15)),
    ("tuesday",   date(2026, 6, 16)),
    ("wednesday", date(2026, 6, 17)),  # today IS Wednesday → skip to next
    # Abbreviations (with and without trailing period)
    ("thu",  date(2026, 6, 11)),
    ("thu.", date(2026, 6, 11)),
    ("fri",  date(2026, 6, 12)),
    ("fri.", date(2026, 6, 12)),
    ("sat",  date(2026, 6, 13)),
    ("sat.", date(2026, 6, 13)),
    ("sun",  date(2026, 6, 14)),
    ("sun.", date(2026, 6, 14)),
    ("mon",  date(2026, 6, 15)),
    ("mon.", date(2026, 6, 15)),
    ("tue",  date(2026, 6, 16)),
    ("tue.", date(2026, 6, 16)),
    ("wed",  date(2026, 6, 17)),
    ("wed.", date(2026, 6, 17)),
])
def test_bare_weekday(phrase, expected):
    assert parse_date_phrase(phrase, today=TODAY) == expected


# ---------- qualified weekday (this / next / upcoming) ----------

@pytest.mark.parametrize("phrase,expected", [
    # "this X" and "upcoming X" → same as bare weekday
    ("this friday",    date(2026, 6, 12)),
    ("this monday",    date(2026, 6, 15)),
    ("this wednesday", date(2026, 6, 17)),
    ("upcoming friday",  date(2026, 6, 12)),
    ("upcoming monday",  date(2026, 6, 15)),
    # "next X" → one full week after the bare result
    ("next thursday",  date(2026, 6, 18)),
    ("next friday",    date(2026, 6, 19)),
    ("next monday",    date(2026, 6, 22)),
    ("next wednesday", date(2026, 6, 24)),
    # abbreviations work too
    ("next fri",       date(2026, 6, 19)),
    ("this fri",       date(2026, 6, 12)),
])
def test_qualified_weekday(phrase, expected):
    assert parse_date_phrase(phrase, today=TODAY) == expected


# ---------- N-unit relative offsets ----------

@pytest.mark.parametrize("phrase,expected", [
    # days
    ("in 1 day",         date(2026, 6, 11)),
    ("in 2 days",        date(2026, 6, 12)),
    ("in 7 days",        date(2026, 6, 17)),
    ("1 day from now",   date(2026, 6, 11)),
    ("3 days from now",  date(2026, 6, 13)),
    # weeks
    ("in 1 week",        date(2026, 6, 17)),
    ("in 2 weeks",       date(2026, 6, 24)),
    ("1 week from now",  date(2026, 6, 17)),
    ("2 weeks from now", date(2026, 6, 24)),
    ("a week from now",  date(2026, 6, 17)),
    # months
    ("in 1 month",       date(2026, 7, 10)),
    ("in 2 months",      date(2026, 8, 10)),
    ("1 month from now", date(2026, 7, 10)),
    ("a month from now", date(2026, 7, 10)),
])
def test_relative_offsets(phrase, expected):
    assert parse_date_phrase(phrase, today=TODAY) == expected


# ---------- period anchors ----------

@pytest.mark.parametrize("phrase,expected", [
    ("end of week", date(2026, 6, 12)),   # Friday of current week
    ("eow",         date(2026, 6, 12)),
    ("end of month", date(2026, 6, 30)),
    ("eom",          date(2026, 6, 30)),
    ("next month",   date(2026, 7,  1)),  # first day of next month
])
def test_period_anchors(phrase, expected):
    assert parse_date_phrase(phrase, today=TODAY) == expected


# ---------- first <weekday> of next month ----------

@pytest.mark.parametrize("phrase,expected", [
    ("first friday of next month", date(2026, 7, 3)),
    ("first monday of next month", date(2026, 7, 6)),
    ("first sunday of next month", date(2026, 7, 5)),
])
def test_first_weekday_of_next_month(phrase, expected):
    assert parse_date_phrase(phrase, today=TODAY) == expected


# ---------- no match → None ----------

@pytest.mark.parametrize("phrase", [
    "buy milk",
    "finish the report",
    "call dentist",
    "something random",
    "",
    "prioritize",
])
def test_no_match_returns_none(phrase):
    assert parse_date_phrase(phrase, today=TODAY) is None


# ---------- extract_date_from_text ----------

@pytest.mark.parametrize("text,exp_text,exp_date", [
    ("dentist friday",             "dentist",         date(2026, 6, 12)),
    ("friday dentist",             "dentist",         date(2026, 6, 12)),
    ("call mom tomorrow",          "call mom",        date(2026, 6, 11)),
    ("review pr tmr",              "review pr",       date(2026, 6, 11)),
    ("submit report in 3 days",    "submit report",   date(2026, 6, 13)),
    ("dentist 2 weeks from now",   "dentist",         date(2026, 6, 24)),
    ("finish project next monday", "finish project",  date(2026, 6, 22)),
    ("team meeting this thursday", "team meeting",    date(2026, 6, 11)),
    ("wrap up eow",                "wrap up",         date(2026, 6, 12)),
    ("pay rent eom",               "pay rent",        date(2026, 6, 30)),
    ("dentist today",              "dentist",         date(2026, 6, 10)),
])
def test_extract_removes_phrase_and_returns_date(text, exp_text, exp_date):
    result_text, result_date = extract_date_from_text(text, today=TODAY)
    assert result_text == exp_text
    assert result_date == exp_date


@pytest.mark.parametrize("text", [
    "buy milk",
    "call dentist",
    "read book",
    "",
])
def test_extract_no_match_unchanged(text):
    result_text, result_date = extract_date_from_text(text, today=TODAY)
    assert result_text == text
    assert result_date is None


# ---------- ordinal day of month ----------

@pytest.mark.parametrize("phrase,expected", [
    # future or today → current month
    ("14th",        date(2026, 6, 14)),
    ("the 14th",    date(2026, 6, 14)),
    ("on the 14th", date(2026, 6, 14)),
    ("22nd",        date(2026, 6, 22)),
    ("10th",        date(2026, 6, 10)),  # today's date is still valid
    # already past in current month → next month
    ("9th",         date(2026, 7,  9)),
    ("1st",         date(2026, 7,  1)),
    ("on the 3rd",  date(2026, 7,  3)),
    # day exceeds days in current month → next month
    ("31st",        date(2026, 7, 31)),
])
def test_ordinal_day_of_month(phrase, expected):
    assert parse_date_phrase(phrase, today=TODAY) == expected


@pytest.mark.parametrize("phrase,expected", [
    ("next month 14th",           date(2026, 7, 14)),
    ("next month the 14th",       date(2026, 7, 14)),
    ("14th of next month",        date(2026, 7, 14)),
    ("the 14th of next month",    date(2026, 7, 14)),
    ("on the 14th of next month", date(2026, 7, 14)),
    ("1st of next month",         date(2026, 7,  1)),
])
def test_ordinal_day_of_next_month(phrase, expected):
    assert parse_date_phrase(phrase, today=TODAY) == expected


# ---------- extract_date_from_text — ordinals ----------

@pytest.mark.parametrize("text,exp_text,exp_date", [
    ("dentist on the 14th",        "dentist",  date(2026, 6, 14)),
    ("dentist the 22nd",           "dentist",  date(2026, 6, 22)),
    ("pay rent 1st of next month", "pay rent", date(2026, 7,  1)),
    ("call mom next month 14th",   "call mom", date(2026, 7, 14)),
])
def test_extract_ordinal(text, exp_text, exp_date):
    result_text, result_date = extract_date_from_text(text, today=TODAY)
    assert result_text == exp_text
    assert result_date == exp_date


# ---------- named month ----------

@pytest.mark.parametrize("phrase,expected", [
    # month + day, future → current year
    ("june 14",       date(2026, 6, 14)),
    ("june 14th",     date(2026, 6, 14)),
    ("jun 14",        date(2026, 6, 14)),
    ("jun 14th",      date(2026, 6, 14)),
    ("June 14",       date(2026, 6, 14)),   # case insensitive
    ("JUNE 14",       date(2026, 6, 14)),
    ("july 4",        date(2026, 7,  4)),
    ("december 25",   date(2026, 12, 25)),
    ("dec 25",        date(2026, 12, 25)),
    # today's date
    ("june 10",       date(2026, 6, 10)),
    # past in current year → roll to next year
    ("june 9",        date(2027, 6,  9)),
    ("may 15",        date(2027, 5, 15)),
    ("january 1",     date(2027, 1,  1)),
    ("jan 1",         date(2027, 1,  1)),
    # day + month formats
    ("14 june",       date(2026, 6, 14)),
    ("14th june",     date(2026, 6, 14)),
    ("14th of june",  date(2026, 6, 14)),
    ("3rd of jul",    date(2026, 7,  3)),
])
def test_named_month(phrase, expected):
    assert parse_date_phrase(phrase, today=TODAY) == expected


@pytest.mark.parametrize("text,exp_text,exp_date", [
    ("dentist june 14",        "dentist",  date(2026, 6, 14)),
    ("pay bills july 4th",     "pay bills", date(2026, 7,  4)),
    ("birthday 14th of june",  "birthday", date(2026, 6, 14)),
    ("submit jan 1",           "submit",   date(2027, 1,  1)),
])
def test_extract_named_month(text, exp_text, exp_date):
    result_text, result_date = extract_date_from_text(text, today=TODAY)
    assert result_text == exp_text
    assert result_date == exp_date
