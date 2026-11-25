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
        self._prefix = {}
        for line_id, rows in self.events.items():
            times = self._times[line_id]
            prefix = [0.0]
            for index in range(1, len(rows)):
                running = (times[index] - times[index-1]).total_seconds()/3600 if rows[index-1].state == 'RUNNING' else 0.0
                prefix.append(prefix[-1] + running)
            self._prefix[line_id] = prefix

    def _integral(self, line_id, at):
        times = self._times.get(line_id, [])
        index = bisect_right(times, at)-1
        if index < 0:
            return 0.0
        tail = (at-times[index]).total_seconds()/3600 if self.events[line_id][index].state == 'RUNNING' else 0.0
        return self._prefix[line_id][index] + tail

    def measure(self, line_id, start, end=None):
        start, end = utc_naive(start), utc_naive(end or datetime.utcnow())
        elapsed = max(0.0,(end-start).total_seconds()/3600)
        if end < start:
            return dict(hours=None, known_hours=0.0, complete=False, elapsed_hours=0.0)
        times = self._times.get(line_id, [])
        complete = bool(times) and times[0] <= start
        known = max(0.0, self._integral(line_id,end)-self._integral(line_id,start))
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
        # A legacy zero is not evidence of a known-zero pre-register lifetime.
        # Existing stand/guide baselines were not verified during import.
        history_complete = bool(readings) and all(x['complete'] for x in readings)
        return dict(lifetime_hours=None, measured_lifetime_hours=known,
                    lifetime_complete=False, measured_history_complete=history_complete,
                    legacy_lifetime_hours=stand.lifetime_hours)
