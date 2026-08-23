from sqlalchemy.orm import Session
from app.models.activity_log import ActivityLog

class OperationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_activity_log(self, log: ActivityLog) -> ActivityLog:
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log