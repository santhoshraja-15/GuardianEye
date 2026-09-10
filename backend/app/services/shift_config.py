"""
Configurable Shift Definition Layer

Warehouse shift boundaries are not stored per-event in the database (the
data model has no `shift` column) — they're a site-configuration concept,
not a fact about a detected behaviour. Rather than hardcode "is this a
morning or evening event" logic wherever a query needs it, every caller
(the temporal analytics service, the assistant's intent resolver) goes
through this single module. Changing a warehouse's shift schedule means
editing SHIFT_DEFINITIONS here once, not hunting through query code.

All resolution happens against `datetime`s already in the database
(`created_at` is UTC on every model via `Base`), so callers get back
timezone-aware ranges ready to filter a query with.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class ShiftDefinition:
    code: str
    label: str
    start_hour: int  # 0-23, inclusive
    end_hour: int  # 0-23, exclusive; end_hour <= start_hour means it wraps past midnight


# The one place to edit if a warehouse's shift schedule changes.
SHIFT_DEFINITIONS: List[ShiftDefinition] = [
    ShiftDefinition(code="MORNING", label="Morning Shift", start_hour=6, end_hour=14),
    ShiftDefinition(code="EVENING", label="Evening Shift", start_hour=14, end_hour=22),
    ShiftDefinition(code="NIGHT", label="Night Shift", start_hour=22, end_hour=6),
]


def _shift_start_dt(on_date: date, shift: ShiftDefinition) -> datetime:
    return datetime.combine(on_date, time(hour=shift.start_hour), tzinfo=timezone.utc)


def _shift_end_dt(on_date: date, shift: ShiftDefinition) -> datetime:
    if shift.end_hour <= shift.start_hour:
        # Wraps past midnight (e.g. Night 22:00 -> 06:00 next day).
        return datetime.combine(on_date + timedelta(days=1), time(hour=shift.end_hour), tzinfo=timezone.utc)
    return datetime.combine(on_date, time(hour=shift.end_hour), tzinfo=timezone.utc)


def get_shift_for_datetime(moment: datetime) -> ShiftDefinition:
    """Which configured shift a given UTC instant falls into."""
    hour = moment.hour
    for shift in SHIFT_DEFINITIONS:
        if shift.start_hour < shift.end_hour:
            if shift.start_hour <= hour < shift.end_hour:
                return shift
        else:
            # Wrapping shift (e.g. 22 -> 6): true if hour is on either side of midnight.
            if hour >= shift.start_hour or hour < shift.end_hour:
                return shift
    return SHIFT_DEFINITIONS[0]


def shift_range_for_date(on_date: date, shift: ShiftDefinition) -> Tuple[datetime, datetime]:
    """The [start, end) datetime bounds of `shift` on the calendar date it *starts*."""
    return _shift_start_dt(on_date, shift), _shift_end_dt(on_date, shift)


def current_shift_range(now: datetime) -> Tuple[datetime, datetime, str]:
    """The bounds of whichever shift `now` falls in, clipped so it never extends past `now`."""
    shift = get_shift_for_datetime(now)
    # A night shift active at 02:00 actually started the previous calendar day.
    start_date = now.date() if now.hour >= shift.start_hour or shift.start_hour < shift.end_hour else now.date() - timedelta(days=1)
    start, end = shift_range_for_date(start_date, shift)
    return start, min(end, now), shift.label


def previous_shift_range(now: datetime) -> Tuple[datetime, datetime, str]:
    """The bounds of the shift immediately preceding the current one."""
    current_start, _current_end, _label = current_shift_range(now)
    shift = get_shift_for_datetime(current_start)
    idx = SHIFT_DEFINITIONS.index(shift)
    prev_shift = SHIFT_DEFINITIONS[idx - 1]  # wraps to the last shift if idx == 0

    # The previous shift ends exactly when the current one starts.
    prev_end = current_start
    prev_start = prev_end - timedelta(hours=_shift_duration_hours(prev_shift))
    return prev_start, prev_end, f"Previous {prev_shift.label}"


def named_shift_range_today(now: datetime, shift_code: str) -> Optional[Tuple[datetime, datetime, str]]:
    """The most relevant occurrence of an explicitly named shift (e.g. 'MORNING')
    relative to `now`, clipped so it never extends into the future.

    Two things this has to get right for a wrapping shift like Night
    (22:00 -> 06:00): asking about it at 02:00 means the one that started
    *yesterday* (still ongoing), not a fictitious one starting later
    today; asking about it at 08:00 (after it ended) means tonight's,
    which hasn't started yet — so it's returned unclipped (0 rows) rather
    than an inverted end-before-start range.
    """
    for shift in SHIFT_DEFINITIONS:
        if shift.code != shift_code:
            continue
        wraps = shift.end_hour <= shift.start_hour
        anchor_date = now.date() - timedelta(days=1) if wraps and now.hour < shift.end_hour else now.date()
        start, end = shift_range_for_date(anchor_date, shift)
        if start > now:
            return start, end, shift.label
        return start, min(end, now), shift.label
    return None


def _shift_duration_hours(shift: ShiftDefinition) -> float:
    if shift.end_hour <= shift.start_hour:
        return (24 - shift.start_hour) + shift.end_hour
    return shift.end_hour - shift.start_hour
