from sqlalchemy.orm import Session
from app.models.stand_asset import StandAsset

class StandRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_code(self, code: str) -> StandAsset | None:
        return self.db.query(StandAsset).filter(StandAsset.code == code).first()

    def get_by_id(self, stand_id: int) -> StandAsset | None:
        return self.db.query(StandAsset).filter(StandAsset.id == stand_id).first()

    def update(self, stand: StandAsset) -> StandAsset:
        self.db.commit()
        self.db.refresh(stand)
        return stand