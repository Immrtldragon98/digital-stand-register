"""Identity-based component histories; new stock issues happen once, atomically."""
from datetime import datetime
from collections import Counter
from fastapi import HTTPException
from app.models.component_asset import ComponentAsset, ComponentFitting, PreparationAssetSelection
from app.models.stand_component import StandComponentPreparation, StandComponentType
from app.models.stand_installation import StandInstallation
from app.models.stand_position import Position
from app.models.inventory_item import InventoryItem
from app.models.inventory_transaction import InventoryTransaction
from app.services.runtime_service import RuntimeService


class ComponentLifecycleService:
    def __init__(self, db):
        self.db = db
        self.runtime = RuntimeService(db)
        self._fittings = None
        self._installations = None
        self._positions = None

    def preload_assets(self, assets):
        asset_ids = [asset.id for asset in assets]
        fittings = self.db.query(ComponentFitting).filter(ComponentFitting.asset_id.in_(asset_ids)).all()
        self._fittings = {}
        for fitting in fittings:
            self._fittings.setdefault(fitting.asset_id, []).append(fitting)
        stand_ids = sorted({fitting.stand_id for fitting in fittings})
        self._installations = {}
        for installation in self.db.query(StandInstallation).filter(StandInstallation.stand_id.in_(stand_ids)).all():
            self._installations.setdefault(installation.stand_id, []).append(installation)
        self._positions = {position.id:position for position in self.db.query(Position).all()}


    def asset_life(self, asset, at=None):
        at = at or datetime.utcnow()
        known = 0.0
        complete = asset.prior_life_hours is not None
        if self._fittings is None:
            self.preload_assets([asset])
        fittings = self._fittings.get(asset.id, [])
        for fitting in fittings:
            stop = min(at, fitting.removed_at or at)
            installs = self._installations.get(fitting.stand_id, [])
            for installation in installs:
                start = max(fitting.fitted_at, installation.installed_at)
                end = min(stop, installation.removed_at or at)
                if end <= start:
                    continue
                position = self._positions.get(installation.position_id)
                if not position:
                    complete = False
                    continue
                measured = self.runtime.measure(position.line_id, start, end)
                known += measured['known_hours']
                complete = complete and measured['complete']
        known = round(known, 3)
        return {'measured_life_hours': round((asset.prior_life_hours or 0) + known, 3) if complete else None,
                'known_runtime_hours': known, 'life_complete': complete,
                'prior_life_hours': asset.prior_life_hours}

    def asset_payload(self, asset, stand_id=None):
        if self._fittings is None:
            self.preload_assets([asset])
        fitting = next((f for f in self._fittings.get(asset.id, []) if f.removed_at is None), None)
        return {'id': asset.id, 'code': asset.code, 'component_type_id': asset.component_type_id,
                'condition': asset.condition, 'current_stand_id': fitting.stand_id if fitting else None,
                'available': fitting is None or fitting.stand_id == stand_id, **self.asset_life(asset)}

    def finalize_preparation(self, stand, at, operator):
        # Caller already locks stand and owns the transaction. No commit here.
        prep = self.db.query(StandComponentPreparation).filter_by(stand_id=stand.id, finalized_at=None).order_by(
            StandComponentPreparation.created_at.desc(), StandComponentPreparation.id.desc()).with_for_update().first()
        if prep is None:
            return {'issued': 0, 'fitted': 0}
        if prep.state == 'SKIPPED':
            if not (prep.notes or '').strip():
                raise HTTPException(400, 'Skipping component tracking requires a reason.')
            prep.finalized_at = at
            return {'issued': 0, 'fitted': 0, 'tracking': 'SKIPPED'}
        selections = self.db.query(PreparationAssetSelection).filter_by(preparation_id=prep.id).all()
        wanted = {selection.asset_id: selection.component_type_id for selection in selections}
        expected = sum(row.new_qty + row.reused_qty for row in prep.items)
        if expected == 0:
            raise HTTPException(400, 'Record component identities or explicitly skip tracking with a reason.')
        if expected != len(wanted):
            raise HTTPException(400, 'Select an individual component identity for every new or reused component.')
        types = {t.id: t for t in self.db.query(StandComponentType).filter(StandComponentType.id.in_(
            sorted(set(wanted.values())))).all()}
        inventory_ids = sorted({t.inventory_item_id for t in types.values() if t.inventory_item_id is not None})
        inventories = {i.id: i for i in self.db.query(InventoryItem).filter(
            InventoryItem.id.in_(inventory_ids)).order_by(InventoryItem.id).with_for_update().all()}
        assets = {a.id: a for a in self.db.query(ComponentAsset).filter(
            ComponentAsset.id.in_(sorted(wanted))).order_by(ComponentAsset.id).with_for_update().all()}
        if len(assets) != len(wanted):
            raise HTTPException(400, 'A selected component asset no longer exists.')
        old = self.db.query(ComponentFitting).filter_by(stand_id=stand.id, removed_at=None).with_for_update().all()
        active = self.db.query(ComponentFitting).filter(ComponentFitting.asset_id.in_(sorted(wanted)),
            ComponentFitting.removed_at.is_(None)).with_for_update().all()
        if any(f.stand_id != stand.id for f in active):
            raise HTTPException(409, 'A selected component is fitted to another stand. Refresh identities.')
        counts = Counter()
        for asset_id, type_id in wanted.items():
            asset = assets[asset_id]
            if asset.component_type_id != type_id:
                raise HTTPException(400, 'Selected identity has the wrong component type.')
            counts[(type_id, asset.condition)] += 1
        issues = Counter()
        for row in prep.items:
            if counts[(row.component_type_id, 'NEW')] != row.new_qty or counts[(row.component_type_id, 'REUSED')] != row.reused_qty:
                raise HTTPException(409, 'Component conditions changed since preparation. Review selections.')
            if row.new_qty:
                component = types[row.component_type_id]
                item = inventories.get(component.inventory_item_id)
                if not item or not item.is_active or item.quantity is None:
                    raise HTTPException(400, f'{component.name}: map a verified preparation-stock balance before fitting new components.')
                issues[item.id] += row.new_qty
        for item_id, qty in issues.items():
            if inventories[item_id].quantity < qty:
                raise HTTPException(409, f'Insufficient preparation stock for {inventories[item_id].name}.')
        # Validate everything first. Flush old assignments before creating new ones.
        for fitting in old:
            fitting.removed_at = at
        self.db.flush()
        for item_id, qty in issues.items():
            item = inventories[item_id]
            before = item.quantity
            item.quantity -= qty
            self.db.add(InventoryTransaction(item_id=item.id, quantity_before=before, quantity_change=-qty,
                quantity_after=item.quantity, operator=operator, reason=f'Stand {stand.code} preparation {prep.id}',
                transaction_type='PREPARATION_ISSUE'))
        for asset_id in wanted:
            assets[asset_id].condition = 'REUSED'
            self.db.add(ComponentFitting(asset_id=asset_id, stand_id=stand.id, preparation_id=prep.id, fitted_at=at))
        prep.finalized_at = at
        prep.state = 'FINALIZED'
        self.db.flush()
        return {'issued': sum(issues.values()), 'fitted': len(wanted)}
