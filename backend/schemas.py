from pydantic import BaseModel, EmailStr

# What the client sends
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    degree: str = "general"
    gender: str = "neutral"
    
# What the server sends back (we avoid sending a password hash)
class UserOut(BaseModel):
    id:int
    username: str
    email: str
    degree: str
    gender: str
    
    class Config:
        from_attributes = True # lets this read directly from a SQLAlchemy object
        
        
class LoginRequest(BaseModel):
    username: str
    password: str
    
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"