"""FastAPI auth dependencies — cookie-based JWT."""
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.exceptions import NotAuthenticatedException
from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User


def _get_user_from_request(request: Request, db: Session) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    user = db.query(User).filter_by(id=int(payload.get("sub", 0))).first()
    if not user or not user.is_active:
        return None
    return user


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """API dependency — returns 401 JSON if unauthenticated."""
    from fastapi import HTTPException
    user = _get_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return user


def get_current_user_or_redirect(request: Request, db: Session = Depends(get_db)) -> User:
    """UI dependency — redirects to /login if unauthenticated."""
    user = _get_user_from_request(request, db)
    if not user:
        raise NotAuthenticatedException(redirect_url=f"/login?next={request.url.path}")
    return user


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    return _get_user_from_request(request, db)


# Annotated aliases for injection
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserUI = Annotated[User, Depends(get_current_user_or_redirect)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
