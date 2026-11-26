from collections import defaultdict
from datetime import datetime, timedelta
from statistics import mean, median
from app.models.inventory_item import InventoryItem
from app.models.line import Line
from app.models.plant_measurement import MaintenanceMeasurement, PreparationCycle, RuntimeConfirmation, ValueBaseline
from app.models.stand_installation import StandInstallation
from app.models.stand_asset import StandAsset
from app.services.evidence_service import bounded_rows
from app.services.runtime_service import RuntimeService


def stats(values):
    return {'samples':len(values),'average':round(mean(values),2) if values else None,'median':round(median(values),2) if values else None}


class PlantValueService:
    def __init__(self, db):
        self.db = db

    def summary(self, days=30, now=None):
        now=now or datetime.utcnow();since=now-timedelta(days=days)
        runtime=RuntimeService(self.db)
        active=self.db.query(StandInstallation).filter(StandInstallation.removed_at.is_(None)).all()
        readings=[runtime.installation(row,now) for row in active]
        confirmations=defaultdict(lambda:None)
        for row in self.db.query(RuntimeConfirmation).order_by(RuntimeConfirmation.confirmed_at).all():
            confirmations[row.line_id]=row
        lines=[]
        for line in self.db.query(Line).order_by(Line.id).all():
            events=runtime.events[line.id];last=events[-1] if events else None;confirmed=confirmations[line.id]
            if confirmed and (last is None or confirmed.state!=last.state or confirmed.confirmed_at<last.event_at):confirmed=None
            checked=max([stamp for stamp in [last.event_at if last else None,confirmed.confirmed_at if confirmed else None] if stamp],default=None)
            lines.append({'id':line.id,'name':line.name,'state':last.state if last else 'UNKNOWN',
                'last_confirmed_at':checked,'needs_confirmation':checked is None or now-checked>timedelta(hours=8),
                'tracking_started_at':events[0].event_at if events else None})
        cycles,cycles_cut=bounded_rows(self.db.query(PreparationCycle).filter(PreparationCycle.finished_at>=since,PreparationCycle.finished_at<=now).order_by(PreparationCycle.finished_at.desc()))
        preparation=[(row.finished_at-row.started_at).total_seconds()/3600 for row in cycles if row.finished_at>=row.started_at]
        measures,measure_cut=bounded_rows(self.db.query(MaintenanceMeasurement).filter(MaintenanceMeasurement.recorded_at>=since,MaintenanceMeasurement.recorded_at<=now).order_by(MaintenanceMeasurement.recorded_at.desc()))
        investigation=[row.duration_minutes for row in measures if row.kind=='INVESTIGATION' and row.duration_minutes is not None]
        shortages=[row for row in measures if row.kind=='SPARE_SHORTAGE']
        inventory=self.db.query(InventoryItem).filter(InventoryItem.is_active.is_(True)).order_by(InventoryItem.name).all()
        risk=[{'id':row.id,'name':row.name,'quantity':row.quantity,'minimum':row.minimum_quantity} for row in inventory if row.quantity is not None and (row.quantity<=0 or row.quantity<row.minimum_quantity)]
        records,record_cut=bounded_rows(self.db.query(StandInstallation).filter(StandInstallation.installed_at>=since,StandInstallation.installed_at<=now).order_by(StandInstallation.installed_at.desc()))
        complete=sum(bool(row.installed_by and row.installed_by.strip()) and (row.removed_at is None or bool(row.removed_by and row.removed_by.strip() and row.removal_reason and row.removal_reason.strip())) for row in records)
        observed={'preparation_hours':stats(preparation),'investigation_minutes':stats(investigation),
            'reported_shortages':len(shortages),'reported_delay_minutes':round(sum(row.duration_minutes for row in shortages if row.duration_minutes is not None),2),
            'shortages_with_duration':sum(row.duration_minutes is not None for row in shortages),
            'record_completeness':{'complete':complete,'total':len(records),'percent':round(complete/len(records)*100,1) if records else None}}
        estimates=[]
        for baseline in self.db.query(ValueBaseline).all():
            current=observed['preparation_hours'] if baseline.metric=='PREPARATION_HOURS' else observed['investigation_minutes']
            estimates.append({'metric':baseline.metric,'baseline':baseline.value,'baseline_samples':baseline.sample_count,
                'baseline_period_start':baseline.period_start,'baseline_period_end':baseline.period_end,'source':baseline.source,
                'current_average':current['average'],'current_samples':current['samples'],
                'estimated_reduction_per_case':round(baseline.value-current['average'],2) if current['average'] is not None else None,
                'basis':'User-supplied baseline minus current observed average; comparable operating conditions are not established. This is an estimate, not verified savings.'})
        return {'as_of':now,'days':days,'lines':lines,'installed':len(active),
            'ready_stands':self.db.query(StandAsset).filter(StandAsset.current_status=='READY').count(),
            'runtime':{'complete_campaigns':sum(row['complete'] for row in readings),'total_campaigns':len(readings),
                'covered_elapsed_hours':round(sum(row['covered_elapsed_hours'] for row in readings),2),
                'installation_elapsed_hours':round(sum(row['elapsed_hours'] for row in readings),2),'confirmation_target_hours':8},
            'observed':observed,'estimates':estimates,'stock':{'at_risk':risk,'unknown_balances':sum(row.quantity is None for row in inventory),'total_items':len(inventory)},
            'recent_measurements':[{'id':row.id,'kind':row.kind,'duration_minutes':row.duration_minutes,'description':row.description,'recorded_by':row.recorded_by,'recorded_at':row.recorded_at} for row in measures[:30]],
            'truncated':{'preparation':cycles_cut,'measurements':measure_cut,'installations':record_cut},
            'method_note':'Preparation is calendar elapsed from explicit Start preparation to Ready, including pauses; old cycles are not invented. Investigation effort and shortage delays are operator-reported minutes. Zero reported incidents does not prove zero incidents. Completeness checks attribution and removal reason, not the physical accuracy of imported history. Runtime confirmations check the current state only; they do not fill historical gaps.'}
