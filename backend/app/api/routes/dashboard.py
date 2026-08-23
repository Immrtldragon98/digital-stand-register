from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.dashboard_service import DashboardService

router = APIRouter()

@router.get("/")
def get_dashboard_data(db: Session = Depends(get_db)):
    service = DashboardService(db)
    return service.get_plant_dashboard()