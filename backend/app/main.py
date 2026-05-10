from fastapi import FastAPI
from app.api.v1 import users
from app.db.session import engine
from app.db.base import Base

app = FastAPI(title="DE个人网站", version="0.0.1")

# 所有 v1 接口都以 /api/v1 为前缀
app.include_router(users.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Hello DEhub!"}