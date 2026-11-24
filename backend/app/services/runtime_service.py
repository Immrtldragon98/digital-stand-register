"""Integrate measured states only. No inferred 24/7 history or scheduled-stop deductions."""
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime, timezone
from app.models.line_runtime import LineRuntimeEvent
from app.models.stand_position import Position
from app.models.stand_installation import StandInstallation


def utc_naive(value):
    return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value


class RuntimeService:
    def __init__(self, db):
        self.db = db
        self.events = defaultdict(list)
        for event in db.query(LineRuntimeEvent).order_by(LineRuntimeEvent.line_id, LineRuntimeEvent.event_at, LineRuntimeEvent.id).all():
            self.events[event.line_id].append(event)
        self.positions = {p.id: p.line_id for p in db.query(Position).all()}
        self._times = {line: [utc_naive(e.event_at) for e in rows] for line, rows in self.events.items()}

    def measure(self, line_id, start, end=None):
        start, end = utc_naive(start), utc_naive(end or datetime.utcnow())
        elapsed = max(0.0,(end-start).total_seconds()/3600)
        if end < start:
            return dict(hours=None, known_hours=0.0, complete=False, elapsed_hours=0.0)
        rows = self.events.get(line_id, [])
        times = self._times.get(line_id, [])
        index = bisect_right(times, start)-1
        complete = index >= 0
        known = 0.0
        if index < 0:
            index = 0
            cursor = times[0] if times else end
        else:
            cursor = start
        while index < len(rows) and cursor < end:
            next_at = times[index+1] if index+1 < len(rows) else end
            until = min(end,next_at)
            if rows[index].state == 'RUNNING':
                known += max(0.0,(until-cursor).total_seconds()/3600)
            cursor = until
            index += 1
        known = round(known,4)
        return dict(hours=known if complete else None,known_hours=known,complete=complete,elapsed_hours=round(elapsed,4))

    interval = measure

    def installation(self, item, now=None):
        return self.measure(self.positions.get(item.position_id),item.installed_at,item.removed_at or now)

    def stand_runtime(self, stand, installations=None, now=None):
        if installations is None:
            installations = self.db.query(StandInstallation).filter_by(stand_id=stand.id).all()
        readings = [self.installation(item,now) for item in installations]
        known = round(sum(x['known_hours'] for x in readings),4)
        # Legacy lifetime may include service before available installation history.
        complete = bool(readings) and all(x['complete'] for x in readings) and not (stand.lifetime_hours or 0)
        return dict(lifetime_hours=known if complete else None, measured_lifetime_hours=known,
                    lifetime_complete=complete,legacy_lifetime_hours=stand.lifetime_hours)
