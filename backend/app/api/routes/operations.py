from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.operation_service import OperationService
from app.schemas.operation import (
    InstallStandSchema,
    RemoveStandSchema,
    MarkReadySchema,
    UpdatePreparationStatusSchema,
    ChangeStandSchema,
)

router = APIRouter()


@router.post("/stands/install")
def install_stand(payload: InstallStandSchema, db: Session = Depends(get_db)):
    return OperationService(db).install_stand(payload.stand_code, payload.position_id, None, payload.operator_name)


@router.post("/stands/remove")
def remove_stand(payload: RemoveStandSchema, db: Session = Depends(get_db)):
    return OperationService(db).remove_stand(payload.stand_code, None, payload.operator_name, payload.reason)


@router.post("/stands/change")
def change_stand(payload: ChangeStandSchema, db: Session = Depends(get_db)):
    return OperationService(db).change_stand(payload, None)


@router.post("/stands/status")
def update_stand_status(payload: UpdatePreparationStatusSchema, db: Session = Depends(get_db)):
    return OperationService(db).update_preparation_status(
        payload.stand_code, payload.status, None, payload.updated_by, payload.remarks
    )


@router.post("/stands/mark-ready")
def mark_stand_ready(payload: MarkReadySchema, db: Session = Depends(get_db)):
    return OperationService(db).mark_stand_ready(payload.stand_code, None, "System")
