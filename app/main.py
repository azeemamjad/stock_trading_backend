# main.py
import os
from fastapi import FastAPI

from app.database import  init_db
from contextlib import asynccontextmanager

from app.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

# 4. Create FastAPI and init tables on startup
app = FastAPI(lifespan=lifespan)

app.include_router(router=router)