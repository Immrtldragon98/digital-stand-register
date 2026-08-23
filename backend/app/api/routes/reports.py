from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.report_service import ReportService

router = APIRouter()


@router.get("/inventory")
def get_inventory_summary(db: Session = Depends(get_db)):
    return ReportService(db).get_asset_inventory_summary()


@router.get("/running-status.xlsx")
def download_running_status(
    year: int = Query(default_factory=lambda: datetime.utcnow().year),
    month: int = Query(default_factory=lambda: datetime.utcnow().month, ge=1, le=12),
    db: Session = Depends(get_db),
):
    try:
        stream = ReportService(db).build_monthly_running_status_xlsx(year, month)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    filename = f"WRM_Stand_Status_{year}-{month:02d}.xlsx"
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
