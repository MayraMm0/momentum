from fastapi import FastAPI, Depends
from backend.database import Base, engine
from backend.routers import users, courses, extracurriculars, meetings, today
from backend.dependencies import get_current_user
from backend.models import User

Base.metadata.create_all(bind = engine)

app = FastAPI(title = "Momentum API")
app.include_router(users.router)
app.include_router(courses.router)
app.include_router(extracurriculars.router)
app.include_router(meetings.router)
app.include_router(today.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to Momentum!"}

# temporary test route
@app.get("/whoami")
def whoami(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "email": current_user.email}