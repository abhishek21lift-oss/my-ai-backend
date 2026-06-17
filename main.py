from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.database import close_db
from routes import chat, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_db()


app = FastAPI(title="My AI Backend", version="1.0.0", lifespan=lifespan)

app.include_router(health.router)
app.include_router(chat.router, prefix="/api/v1")
