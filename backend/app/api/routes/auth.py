from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.services.audit import write_audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: DbSession, request: Request) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not verify_password(body.password, user.password_hash):
        write_audit(
            db,
            action="auth.login_failed",
            target=body.email.lower(),
            result="failure",
            ip_address=request.client.host if request.client else None,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(str(user.id), {"role": user.role, "org": str(user.organization_id)})
    write_audit(
        db,
        action="auth.login",
        user_id=user.id,
        organization_id=user.organization_id,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(user: CurrentUser) -> UserResponse:
    return UserResponse(id=str(user.id), email=user.email, full_name=user.full_name, role=user.role)
