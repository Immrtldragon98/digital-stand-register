"""Bounded evidence windows and date intervals; no inference of actual mill runtime."""
from bisect import bisect_right
from datetime import timedelta

MAX_EVIDENCE_ROWS = 20_000

def bounded_rows(query, maximum=MAX_EVIDENCE_ROWS):
    rows = query.limit(maximum + 1).all()
    return rows[:maximum], len(rows) > maximum

def merge_intervals(windows):
    result = []
    for start, end in sorted((start, end) for start, end in windows if start and end and start <= end):
        if result and start <= result[-1][1]:
            result[-1] = (result[-1][0], max(result[-1][1], end))
        else:
            result.append((start, end))
    return result

def in_intervals(value, intervals):
    if value is None or not intervals:
        return False
    index = bisect_right(intervals, (value, value)) - 1
    # Equal start with a later end sorts after (value,value).
    if index + 1 < len(intervals) and intervals[index + 1][0] == value:
        index += 1
    return index >= 0 and intervals[index][0] <= value <= intervals[index][1]
