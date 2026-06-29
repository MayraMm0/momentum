from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import UserCreate, UserOut, LoginRequest, TokenResponse
from backend.auth import create_access_token
from datetime import datetime, timedelta, timezone
from backend.security import hash_password, verify_password, hash_token
from backend.models import User, Session as SessionModel  # renamed to avoid clashing with SQLAlchemy's Session class
from backend.config import settings
from backend.dependencies import get_current_user

router = APIRouter()

# ==== USER REGISTRATION ENDPOINT ====
@router.post("/register", response_model=UserOut)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username or email already exist
    existing = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    # Create new user
    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password),
        degree=user.degree,
        gender=user.gender,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# ==== USER LOGIN ENDPOINT ====
@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Username or password is incorrect")
    
    token = create_access_token(user.username)
    
    session_row = SessionModel(
        user_id = user.id,
        token_hash = hash_token(token),
        expires_at = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES),
        is_revoked = False
    ) 
    
    db.add(session_row)
    db.commit()
    
    return TokenResponse(access_token = token)

# ==== USER LOGOUT ENDPOINT ====
@router.post("/logout")
def logout(authorization: str = Header(...), db: Session = Depends(get_db)):
    token = authorization.split(" ")[1]
    session_row = db.query(SessionModel).filter(
        SessionModel.token_hash == hash_token(token)
    ).first()
    
    if session_row:
        session_row.is_revoked = True
        db.commit()
        
    return{"message:", "Logged out successfully"}
