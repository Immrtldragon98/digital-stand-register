from sqlalchemy.orm import Session
from app.models.entry_guide_asset import EntryGuideAsset


class EntryGuideRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[EntryGuideAsset]:
        return self.db.query(EntryGuideAsset).order_by(EntryGuideAsset.code).all()

    def get_by_code(self, code: str) -> EntryGuideAsset | None:
        return (
            self.db.query(EntryGuideAsset)
            .filter(EntryGuideAsset.code == code)
            .first()
        )

    def get_by_id(self, guide_id: int) -> EntryGuideAsset | None:
        return (
            self.db.query(EntryGuideAsset)
            .filter(EntryGuideAsset.id == guide_id)
            .first()
        )

    def update(self, guide: EntryGuideAsset) -> EntryGuideAsset:
        self.db.commit()
        self.db.refresh(guide)
        return guide
