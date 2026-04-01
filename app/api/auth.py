"""Authentication endpoints — register, login, demo login, logout, me."""
from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session

from app.core.dependencies import DBSession
from app.core.security import hash_password, verify_password, create_access_token
from app.core.auth_deps import CurrentUser
from app.models.user import User
from app.config import get_settings
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()

_COOKIE = "access_token"
_COOKIE_OPTS = dict(httponly=True, samesite="lax", secure=False)  # set secure=True behind HTTPS


def _set_token_cookie(response: RedirectResponse, user: User) -> None:
    token = create_access_token({"sub": str(user.id), "email": user.email})
    response.set_cookie(_COOKIE, token, max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, **_COOKIE_OPTS)


# ── Register ────────────────────────────────────────────────────────────────

@router.post("/register")
def register(
    db: DBSession,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
):
    email = email.lower().strip()
    if password != confirm_password:
        return RedirectResponse("/register?error=passwords_do_not_match", status_code=303)
    if len(password) < 6:
        return RedirectResponse("/register?error=password_too_short", status_code=303)
    if db.query(User).filter_by(email=email).first():
        return RedirectResponse("/register?error=email_already_exists", status_code=303)
    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name.strip(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("New user registered: %s", email)
    resp = RedirectResponse("/?welcome=1", status_code=303)
    _set_token_cookie(resp, user)
    return resp


# ── Login ────────────────────────────────────────────────────────────────────

@router.post("/login")
def login(
    db: DBSession,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form(default="/"),
):
    email = email.lower().strip()
    user = db.query(User).filter_by(email=email, is_active=True).first()
    if not user or not verify_password(password, user.hashed_password):
        return RedirectResponse("/login?error=invalid_credentials", status_code=303)
    resp = RedirectResponse(next or "/", status_code=303)
    _set_token_cookie(resp, user)
    logger.info("User logged in: %s", email)
    return resp


# ── Demo login ───────────────────────────────────────────────────────────────

@router.post("/demo")
def demo_login(db: DBSession):
    user = db.query(User).filter_by(email=settings.DEMO_EMAIL, is_active=True).first()
    if not user:
        return RedirectResponse("/login?error=demo_unavailable", status_code=303)
    resp = RedirectResponse("/", status_code=303)
    _set_token_cookie(resp, user)
    return resp


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie(_COOKIE)
    return resp


# ── Me ────────────────────────────────────────────────────────────────────────

@router.get("/me")
def me(user: CurrentUser):
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_demo": user.is_demo,
        "is_admin": user.is_admin,
    }
