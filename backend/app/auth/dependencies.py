from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.jwt import decode_access_token
from app.database.session import get_db
from app.models.user import User

ADMIN_ROLE_ID = 1
OPERATOR_ROLE_ID = 2

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_token(token)
    username = payload.get("sub") if payload else None
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please sign in to edit.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_operator(user: User = Depends(get_current_user)) -> User:
    if user.role_id not in {ADMIN_ROLE_ID, OPERATOR_ROLE_ID}:
        raise HTTPException(status_code=403, detail="Operator access required.")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role_id != ADMIN_ROLE_ID:
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user


def role_name(role_id: int) -> str:
    return "ADMIN" if role_id == ADMIN_ROLE_ID else "OPERATOR"
