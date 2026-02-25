from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.user import User, RefreshToken

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "ripple_refresh_token"
COOKIE_MAX_AGE = settings.refresh_token_expire_days * 24 * 60 * 60  # seconds


# ── Helpers ────────────────────────────────────────────────────────────────────

def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=raw_token,
        httponly=True,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/api/v1/auth",
    )


async def _create_tokens(user_id: str, db: AsyncSession) -> tuple[str, str]:
    """Issue a new access + refresh token pair. Stores hashed refresh token in DB."""
    raw_refresh, hashed_refresh = generate_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    db.add(RefreshToken(user_id=user_id, token_hash=hashed_refresh, expires_at=expires_at))
    await db.commit()
    access = create_access_token(user_id)
    return access, raw_refresh


def _user_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
    }


# ── Schemas ────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    existing = await db.scalar(select(User).where(User.email == body.email))
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered.")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        display_name=body.display_name,
    )
    db.add(user)
    await db.flush()  # get user.id without committing

    access, raw_refresh = await _create_tokens(user.id, db)
    _set_refresh_cookie(response, raw_refresh)
    return {"access_token": access, "user": _user_dict(user)}


@router.post("/login")
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == body.email))
    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    access, raw_refresh = await _create_tokens(user.id, db)
    _set_refresh_cookie(response, raw_refresh)
    return {"access_token": access, "user": _user_dict(user)}


@router.get("/me")
async def me(
    response: Response,
    db: AsyncSession = Depends(get_db),
    ripple_refresh_token: str | None = Cookie(default=None),
):
    if not ripple_refresh_token:
        raise HTTPException(status_code=401, detail="Not authenticated.")

    token_hash = hash_refresh_token(ripple_refresh_token)
    token_row = await db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,  # noqa: E712
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
    )
    if not token_row:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")

    user = await db.get(User, token_row.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")

    # Issue a fresh access token (refresh token stays)
    new_access = create_access_token(user.id)
    return {"access_token": new_access, "user": _user_dict(user)}


@router.post("/logout")
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    ripple_refresh_token: str | None = Cookie(default=None),
):
    if ripple_refresh_token:
        token_hash = hash_refresh_token(ripple_refresh_token)
        token_row = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        if token_row:
            token_row.revoked = True
            await db.commit()

    response.delete_cookie(key=REFRESH_COOKIE, path="/api/v1/auth")
    return {"message": "Logged out."}


# ── GitHub OAuth ───────────────────────────────────────────────────────────────

@router.get("/github")
async def github_login():
    """Redirect user to GitHub OAuth page."""
    url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        "&scope=repo,user:email"
    )
    return RedirectResponse(url)


@router.get("/github/callback")
async def github_callback(code: str, response: Response, db: AsyncSession = Depends(get_db)):
    """Exchange GitHub code for access token, upsert user, issue JWT pair."""
    async with httpx.AsyncClient() as client:
        # 1. Exchange code → GitHub access token
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={"client_id": settings.github_client_id, "client_secret": settings.github_client_secret, "code": code},
            headers={"Accept": "application/json"},
        )
        token_data = token_resp.json()
        github_token = token_data.get("access_token")
        if not github_token:
            raise HTTPException(status_code=400, detail="GitHub OAuth failed.")

        # 2. Fetch user profile
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {github_token}", "Accept": "application/json"},
        )
        gh_user = user_resp.json()

        # 3. Get primary email if not public
        email = gh_user.get("email")
        if not email:
            emails_resp = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {github_token}"},
            )
            emails = emails_resp.json()
            primary = next((e for e in emails if e.get("primary")), None)
            email = primary["email"] if primary else f"gh_{gh_user['id']}@ripple.local"

    github_id = str(gh_user["id"])

    # 4. Upsert user
    user = await db.scalar(select(User).where(User.github_id == github_id))
    if not user:
        # Check if email already exists (linked to a password account)
        user = await db.scalar(select(User).where(User.email == email))
    if not user:
        user = User(
            email=email,
            display_name=gh_user.get("name") or gh_user.get("login") or "GitHub User",
            avatar_url=gh_user.get("avatar_url"),
        )
        db.add(user)
        await db.flush()

    user.github_id = github_id
    user.github_access_token = github_token
    if not user.avatar_url:
        user.avatar_url = gh_user.get("avatar_url")

    access, raw_refresh = await _create_tokens(user.id, db)

    # 5. Redirect to frontend with access token; refresh token set in cookie
    redirect = RedirectResponse(url=f"http://localhost:5173/?token={access}")
    redirect.set_cookie(
        key=REFRESH_COOKIE,
        value=raw_refresh,
        httponly=True,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/api/v1/auth",
    )
    return redirect


# ── Auth Dependency (for protected routes) ─────────────────────────────────────

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    # Bearer token is extracted manually (FastAPI doesn't auto-parse it)
    authorization: str | None = None,
) -> User:
    """Use as: current_user: User = Depends(get_current_user)"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header.")
    token = authorization.removeprefix("Bearer ")
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")
    return user
