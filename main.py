from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from routes import chat, health

app = FastAPI(title="My AI Backend", version="1.0.0")

app.include_router(health.router)
app.include_router(chat.router, prefix="/api/v1")
