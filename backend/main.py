from fastapi import FastAPI
from backend.database import Base, engine
from backend.routers import users

Base.metadata.create_all(bind = engine)

app = FastAPI(title = "Momentum API")
app.include_router(users.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Momentum!"}

