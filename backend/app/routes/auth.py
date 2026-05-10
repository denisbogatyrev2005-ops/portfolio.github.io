from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, UserRole
from app.utils.auth import verify_password, hash_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

TEACHER_SECRET_CODE = "TEACHER2026"

def user_dict(user):
    role = user.role.value if hasattr(user.role, 'value') else str(user.role)
    return {"id": user.id, "full_name": user.full_name, "email": user.email, "role": role, "group": user.group}

@router.post("/register")
async def register(request_data: dict, db: Session = Depends(get_db)):
    email = request_data.get("email", "").strip()
    password = request_data.get("password", "")
    full_name = request_data.get("full_name", "").strip()
    role_str = request_data.get("role", "student")
    group = request_data.get("group", "").strip() or None
    secret = request_data.get("secret_code", "")

    if not email or not password or not full_name:
        raise HTTPException(400, "Заполните все поля")
    if len(password) < 6:
        raise HTTPException(400, "Пароль должен быть не менее 6 символов")
    if role_str == "teacher" and secret != TEACHER_SECRET_CODE:
        raise HTTPException(403, "Неверный код преподавателя")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "Email уже зарегистрирован")

    user = User(full_name=full_name, email=email,
                hashed_password=hash_password(password),
                role=UserRole(role_str), group=group)
    db.add(user); db.commit(); db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "user": user_dict(user)}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(401, "Неверный email или пароль")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "user": user_dict(user)}

@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return user_dict(current_user)
