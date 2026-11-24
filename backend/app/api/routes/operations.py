from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.auth.dependencies import require_operator
from app.database.session import get_db
from app.models.user import User
from app.services.operation_service import OperationService
from app.services.command_service import run_command, command_result
from app.schemas.operation import (
    InstallStandSchema,
    RemoveStandSchema,
    MarkReadySchema,
    UpdatePreparationStatusSchema,
    ChangeStandSchema,
)

router = APIRouter()


@router.post("/stands/install")
def install_stand(payload: InstallStandSchema, db: Session = Depends(get_db), user: User = Depends(require_operator), idempotency_key: str | None = Header(default=None)):
    return run_command(db,user.id,idempotency_key,'INSTALL',payload.model_dump(),lambda: OperationService(db,auto_commit=False).install_stand(payload.stand_code,payload.position_id,user.id,payload.operator_name or user.username))


@router.post("/stands/remove")
def remove_stand(payload: RemoveStandSchema, db: Session = Depends(get_db), user: User = Depends(require_operator), idempotency_key: str | None = Header(default=None)):
    return run_command(db,user.id,idempotency_key,'REMOVE',payload.model_dump(),lambda: OperationService(db,auto_commit=False).remove_stand(payload.stand_code,user.id,payload.operator_name or user.username,payload.reason))


@router.post("/stands/change")
def change_stand(payload: ChangeStandSchema, db: Session = Depends(get_db), user: User = Depends(require_operator), idempotency_key: str | None = Header(default=None)):
    return run_command(db,user.id,idempotency_key,'CHANGE',payload.model_dump(),lambda: OperationService(db,auto_commit=False).change_stand(payload,user.id))


@router.post("/stands/status")
def update_stand_status(payload: UpdatePreparationStatusSchema, db: Session = Depends(get_db), user: User = Depends(require_operator), idempotency_key: str | None = Header(default=None)):
    return run_command(db,user.id,idempotency_key,'STATUS',payload.model_dump(),lambda: OperationService(db,auto_commit=False).update_preparation_status(payload.stand_code,payload.status,user.id,payload.updated_by,payload.remarks))


@router.post("/stands/mark-ready")
def mark_stand_ready(payload: MarkReadySchema, db: Session = Depends(get_db), user: User = Depends(require_operator), idempotency_key: str | None = Header(default=None)):
    return run_command(db,user.id,idempotency_key,'READY',payload.model_dump(),lambda: OperationService(db,auto_commit=False).mark_stand_ready(payload.stand_code,user.id,user.username))


@router.get('/commands/{request_key}')
def read_command(request_key: str, db: Session = Depends(get_db), user: User = Depends(require_operator)):
    return command_result(db,user.id,request_key)
