from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.database import close_db
from core.logging_config import configure_logging
from core.redis import close_redis
from exceptions.handlers import register_exception_handlers
from middleware.request_logger import RequestLoggerMiddleware
from routes import chat, health
from routes.agents import router as agents_router
from routes.auth import router as auth_router
from routes.hooks import router as hooks_router
from routes.recommendations import router as recommendations_router
from routes.research import router as research_router
from routes.scripts import router as scripts_router
from routes.topics import router as topics_router
from routes.trends import router as trends_router
from routes.viral_content import router as viral_content_router

configure_logging()

API_V1 = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_db()
    await close_redis()


app = FastAPI(
    title="AI Content Creator Backend",
    version="2.0.0",
    description="Production AI backend for viral content creation",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.add_middleware(RequestLoggerMiddleware)

app.include_router(health.router)
app.include_router(chat.router, prefix=API_V1)
app.include_router(auth_router, prefix=API_V1)
app.include_router(topics_router, prefix=API_V1)
app.include_router(viral_content_router, prefix=API_V1)
app.include_router(trends_router, prefix=API_V1)
app.include_router(research_router, prefix=API_V1)
app.include_router(hooks_router, prefix=API_V1)
app.include_router(scripts_router, prefix=API_V1)
app.include_router(recommendations_router, prefix=API_V1)
app.include_router(agents_router, prefix=API_V1)
