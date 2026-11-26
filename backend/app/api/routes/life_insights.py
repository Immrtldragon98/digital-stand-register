from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.life_insight_service import LifeInsightService

router = APIRouter()

@router.get('/life-insights')
def life_insights(db: Session = Depends(get_db)):
    return LifeInsightService(db).summary()
