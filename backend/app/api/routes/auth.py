from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import ADMIN_ROLE_ID, OPERATOR_ROLE_ID, get_current_user, require_admin, role_name
from app.auth.security import create_access_token, get_password_hash, verify_password
from app.database.session import get_db
from app.models.user import User

router = APIRouter()


class LoginSchema(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class UserCreateSchema(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    role: str = Field(default="OPERATOR")


class PasswordResetSchema(BaseModel):
    password: str = Field(min_length=6, max_length=128)


class RoleUpdateSchema(BaseModel):
    role: str


def _serialize_user(user: User):
    return {
        "id": user.id,
        "username": user.username,
        "role_id": user.role_id,
        "role": role_name(user.role_id),
    }


def _role_id(value: str) -> int:
    role = value.strip().upper()
    if role == "ADMIN":
        return ADMIN_ROLE_ID
    if role == "OPERATOR":
        return OPERATOR_ROLE_ID
    raise HTTPException(400, "Role must be ADMIN or OPERATOR")


@router.post("/login")
def login(payload: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username.strip()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username, "role_id": user.role_id})
    return {"access_token": access_token, "token_type": "bearer", "user": _serialize_user(user)}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return _serialize_user(user)


@router.post("/bootstrap-admin", status_code=201)
def bootstrap_admin(payload: UserCreateSchema, db: Session = Depends(get_db)):
    if db.query(User).count() > 0:
        raise HTTPException(409, "Admin setup is already complete")
    username = payload.username.strip()
    user = User(username=username, hashed_password=get_password_hash(payload.password), role_id=ADMIN_ROLE_ID)
    db.add(user)
    db.commit()
    db.refresh(user)
    access_token = create_access_token(data={"sub": user.username, "role_id": user.role_id})
    return {"access_token": access_token, "token_type": "bearer", "user": _serialize_user(user)}


@router.get("/users")
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return [_serialize_user(user) for user in db.query(User).order_by(User.username).all()]


@router.post("/users", status_code=201)
def create_user(payload: UserCreateSchema, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    username = payload.username.strip()
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(409, "Username already exists")
    user = User(username=username, hashed_password=get_password_hash(payload.password), role_id=_role_id(payload.role))
    db.add(user)
    db.commit()
    db.refresh(user)
    return _serialize_user(user)


@router.patch("/users/{user_id}/role")
def update_user_role(user_id: int, payload: RoleUpdateSchema, db: Session = Depends(get_db), current: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    new_role = _role_id(payload.role)
    if user.id == current.id and new_role != ADMIN_ROLE_ID:
        raise HTTPException(400, "You cannot remove your own admin access")
    if user.role_id == ADMIN_ROLE_ID and new_role != ADMIN_ROLE_ID and db.query(User).filter(User.role_id == ADMIN_ROLE_ID).count() <= 1:
        raise HTTPException(400, "At least one admin must remain")
    user.role_id = new_role
    db.commit()
    db.refresh(user)
    return _serialize_user(user)


@router.patch("/users/{user_id}/password")
def reset_user_password(user_id: int, payload: PasswordResetSchema, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    user.hashed_password = get_password_hash(payload.password)
    db.commit()
    return {"status": "success"}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == current.id:
        raise HTTPException(400, "You cannot delete your own account")
    if user.role_id == ADMIN_ROLE_ID and db.query(User).filter(User.role_id == ADMIN_ROLE_ID).count() <= 1:
        raise HTTPException(400, "At least one admin must remain")
    db.delete(user)
    db.commit()
    return {"status": "success"}
