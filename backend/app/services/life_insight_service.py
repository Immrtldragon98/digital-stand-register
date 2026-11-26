"""Separate ongoing exposure from completed campaign comparisons and measured runtime."""
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo
from datetime import timezone
from math import isfinite
from statistics import mean, median
from sqlalchemy.orm import joinedload
from app.models.line import Line
from app.models.stand_position import Position
from app.models.stand_installation import StandInstallation
from app.models.reliability_history import HistoricalCampaign
from app.services.runtime_service import RuntimeService, utc_naive
from app.services.evidence_service import bounded_rows

MIN_COHORT = 3
BASIS = 'INFERRED_SNAPSHOT_ELAPSED_DAYS'


def dedupe_completed_campaigns(rows, as_of=None):
    clock = as_of or datetime.utcnow()
    today = (clock.replace(tzinfo=timezone.utc) if clock.tzinfo is None else clock).astimezone(ZoneInfo('Asia/Kolkata')).date()
    groups = defaultdict(list)
    excluded = dict(ongoing=0, invalid=0, duplicate=0, conflicting=0)
    for row in rows:
        life = row.life_days
        if row.removed_date is None:
            excluded['ongoing'] += 1
            continue
        if (not row.installed_date or row.removed_date <= row.installed_date or row.removed_date > today
                or life is None or not isfinite(float(life)) or life <= 0
                or abs(float(life)-(row.removed_date-row.installed_date).days) > 0.001):
            excluded['invalid'] += 1
            continue
        groups[(row.line_name, row.position_number, row.stand_code, row.installed_date)].append(row)
    result = []
    for group in groups.values():
        signatures = {(row.removed_date, round(float(row.life_days), 6)) for row in group}
        if len(signatures) > 1:
            excluded['conflicting'] += len(group)
            continue
        result.append(group[0])
        excluded['duplicate'] += len(group)-1
    return result, excluded


def _peer_median(total, excluded):
    """Median after excluding a cohort, without repeatedly copying all peer rows."""
    count = len(total)-len(excluded)
    if not count:
        return None
    def kth(rank):
        low, high = 0, len(total)-1
        while low < high:
            mid = (low+high)//2
            available = bisect_right(total, total[mid])-bisect_right(excluded, total[mid])
            if available >= rank:
                high = mid
            else:
                low = mid+1
        return total[low]
    return (kth((count+1)//2)+kth((count+2)//2))/2


def completed_comparisons(rows):
    by_stand, by_position, by_context, by_number = (defaultdict(list) for _ in range(4))
    for row in rows:
        value = float(row.life_days)
        by_stand[(row.line_name, row.position_number, row.stand_code)].append(value)
        by_position[(row.line_name, row.position_number)].append(value)
        by_context[(row.line_name, row.position_number)].append(value)
        by_number[row.position_number].append(value)
    for collection in (by_stand, by_position, by_context, by_number):
        for values in collection.values():
            values.sort()
    def metrics(values, peers):
        n, peer_count = len(values), len(peers)-len(values)
        med = median(values)
        peer_med = _peer_median(peers, values)
        enough = n >= MIN_COHORT and peer_count >= MIN_COHORT and bool(peer_med)
        return dict(campaigns=n, avg_days=round(mean(values), 2), median_days=round(med, 2),
            min_days=round(values[0], 2), max_days=round(values[-1], 2), peer_campaigns=peer_count,
            peer_median_days=round(peer_med, 2) if peer_med is not None else None,
            vs_peer_pct=round((med/peer_med-1)*100, 1) if enough else None,
            evidence='SUFFICIENT' if enough else 'INSUFFICIENT', basis=BASIS)
    stands = [dict(stand=code, line=line, position=pos, **metrics(values, by_context[(line,pos)]))
              for (line,pos,code), values in by_stand.items()]
    positions = [dict(line=line, position=pos, **metrics(values, by_number[pos]),
        screening_assumption='Other lines at the same numbered position; duty equivalence is unverified.')
        for (line,pos), values in by_position.items()]
    stands.sort(key=lambda row: (row['evidence'] != 'SUFFICIENT', -(row['vs_peer_pct'] or 0), row['line'], row['position'], row['stand']))
    positions.sort(key=lambda row: (row['evidence'] != 'SUFFICIENT', row['vs_peer_pct'] or 0, row['line'], row['position']))
    return stands, positions


class LifeInsightService:
    def __init__(self, db):
        self.db = db

    def summary(self, now=None):
        now = utc_naive(now or datetime.utcnow())
        runtime = RuntimeService(self.db)
        position_rows = self.db.query(Position, Line).join(Line, Position.line_id == Line.id).limit(1000).all()
        positions = {position.id: (position, line.name) for position, line in position_rows}
        active, active_truncated = bounded_rows(self.db.query(StandInstallation)
            .options(joinedload(StandInstallation.stand)).filter(StandInstallation.removed_at.is_(None))
            .order_by(StandInstallation.installed_at, StandInstallation.id), maximum=1000)
        ongoing = []
        for installation in active:
            context = positions.get(installation.position_id)
            if context is None:
                continue
            position, line = context
            reading = runtime.installation(installation, now)
            ongoing.append(dict(stand=installation.stand.code, line=line, position=position.position_number,
                installed_at=installation.installed_at, elapsed_hours=round(reading['elapsed_hours'],2),
                actual_runtime_hours=reading['hours'], known_runtime_hours=reading['known_hours'] if reading['has_coverage'] else None,
                runtime_complete=reading['complete'], coverage_status=reading['coverage_status'],
                observed_from=reading['observed_from'], ongoing=True,
                elapsed_basis='CALENDAR_TIME_SINCE_INSTALLATION_NOT_MILL_RUNTIME'))
        ongoing.sort(key=lambda row: (-row['elapsed_hours'], row['line'], row['position']))
        measured = [row for row in ongoing if row['runtime_complete']]
        measured.sort(key=lambda row: (-(row['actual_runtime_hours'] or 0), row['line'], row['position']))
        history, history_truncated = bounded_rows(self.db.query(HistoricalCampaign)
            .order_by(HistoricalCampaign.installed_date.desc(), HistoricalCampaign.id.desc()))
        completed, exclusions = dedupe_completed_campaigns(history, now)
        stand_rows, position_stats = completed_comparisons(completed)
        registered, registered_truncated = bounded_rows(self.db.query(StandInstallation)
            .options(joinedload(StandInstallation.stand)).filter(StandInstallation.removed_at.isnot(None))
            .order_by(StandInstallation.removed_at.desc(), StandInstallation.id.desc()))
        actual_rows = []
        incomplete = invalid_registered = 0
        for installation in registered:
            context = positions.get(installation.position_id)
            if context is None or installation.removed_at > now or installation.removed_at < installation.installed_at:
                invalid_registered += 1
                continue
            reading = runtime.installation(installation, now)
            if not reading['complete']:
                incomplete += 1
                continue
            position, line = context
            actual_rows.append(SimpleNamespace(line_name=line, position_number=position.position_number,
                stand_code=installation.stand.code, life_days=reading['hours']))
        actual_stands, actual_positions = completed_comparisons(actual_rows)
        def hours_schema(row):
            rename = {'avg_days':'avg_hours', 'median_days':'median_hours', 'min_days':'min_hours',
                      'max_days':'max_hours', 'peer_median_days':'peer_median_hours'}
            return {**{rename.get(key,key):value for key,value in row.items()}, 'basis':'MEASURED_MILL_RUNTIME_HOURS'}
        return dict(as_of=now, ongoing=ongoing, longest_current_installation=ongoing[0] if ongoing else None,
            longest_current_measured=measured[0] if measured else None,
            historical_stand_performance=stand_rows[:200], weak_positions=position_stats[:200],
            measured_completed_stand_performance=[hours_schema(row) for row in actual_stands[:200]],
            measured_weak_positions=[hours_schema(row) for row in actual_positions[:200]],
            measured_completed_campaigns=len(actual_rows), measured_incomplete_campaigns=incomplete,
            measured_invalid_campaigns=invalid_registered,
            exclusions=exclusions, completed_campaigns=len(completed),
            truncated=dict(active=active_truncated, history=history_truncated, registered_history=registered_truncated,
                stand_groups=len(stand_rows)>200, position_groups=len(position_stats)>200,
                measured_stand_groups=len(actual_stands)>200, measured_position_groups=len(actual_positions)>200),
            method_note='Ongoing campaigns are right-censored and excluded from completed averages. Installation elapsed time is calendar exposure, not measured runtime or a failure-life estimate. Historical life is inferred snapshot elapsed days, not measured mill-running hours. Registered completed campaigns with complete runtime coverage are compared separately in measured hours; incomplete campaigns are excluded from measured rankings. Stand comparisons use other stand IDs at the same line and position. Position comparisons use other lines at the same numbered position as screening only; equivalent operating duty is not established. At least 3 completed campaigns in each target and independent peer cohort are required. Longer observed life does not establish greater reliability or predict remaining life.')
