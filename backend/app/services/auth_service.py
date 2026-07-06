from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token, verify_token,
)
from app.core.exceptions import bad_request, unauthorized, not_found


class AuthService:
    """用户认证服务"""

    @staticmethod
    def register(db: Session, username: str, password: str, email: str = None) -> User:
        """用户注册"""
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            raise bad_request("用户名已存在")
        if email:
            existing_email = db.query(User).filter(User.email == email).first()
            if existing_email:
                raise bad_request("邮箱已被使用")

        user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            role="user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def login(db: Session, username: str, password: str) -> tuple[str, str, User]:
        """用户登录，返回 (access_token, refresh_token, user)"""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise unauthorized("用户名或密码错误")
        if not verify_password(password, user.password_hash):
            raise unauthorized("用户名或密码错误")
        if not user.is_active:
            raise unauthorized("账户已被禁用")

        access_token = create_access_token({"sub": str(user.id), "username": user.username, "role": user.role})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        return access_token, refresh_token, user

    @staticmethod
    def refresh_token(db: Session, token: str) -> tuple[str, str]:
        """刷新 Token"""
        payload = verify_token(token, "refresh")
        if payload is None:
            raise unauthorized("无效的刷新令牌")
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            raise unauthorized("用户不存在或已被禁用")

        new_access = create_access_token({"sub": str(user.id), "username": user.username, "role": user.role})
        new_refresh = create_refresh_token({"sub": str(user.id)})
        return new_access, new_refresh

    @staticmethod
    def change_password(db: Session, user: User, old_password: str, new_password: str):
        """修改密码"""
        if not verify_password(old_password, user.password_hash):
            raise bad_request("原密码错误")
        user.password_hash = get_password_hash(new_password)
        db.commit()

    @staticmethod
    def init_admin(db: Session):
        """初始化管理员账号"""
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=get_password_hash("123456"),
                role="admin",
                email="admin@example.com",
            )
            db.add(admin)
            db.commit()
            print("[OK] 管理员账号已创建: admin / 123456")
        return admin