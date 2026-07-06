from fastapi import APIRouter, Depends
from jose import jwt
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import (
    RegisterRequest, LoginRequest, ChangePasswordRequest,
    TokenResponse, UserResponse, RefreshRequest,
)
from app.services.auth_service import AuthService
from app.core.security import get_current_user, verify_token
from app.config import settings
from app.models.user import User

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


@router.post("/register", response_model=TokenResponse, summary="用户注册")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    user = AuthService.register(db, req.username, req.password, req.email)
    access_token, refresh_token, _ = AuthService.login(db, req.username, req.password)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse, summary="用户登录")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    access_token, refresh_token, user = AuthService.login(db, req.username, req.password)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse, summary="刷新 Token")
def refresh(req: RefreshRequest, db: Session = Depends(get_db)):
    access_token, refresh_token = AuthService.refresh_token(db, req.refresh_token)
    payload = verify_token(access_token, "access")
    if payload is None:
        from app.core.exceptions import unauthorized
        raise unauthorized("无效的令牌")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/change-password", summary="修改密码")
def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    AuthService.change_password(db, current_user, req.old_password, req.new_password)
    return {"message": "密码修改成功"}


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)