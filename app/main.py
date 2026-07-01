from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from contextlib import asynccontextmanager
import logging

from app.blocklist import blocklist_manager
from app.ddos_bot import start_bot
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ddos_protection")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Pyrogram on current event loop...")
    await start_bot()
    logger.info("DDoS Protection Bot Started Successfully!")
    yield

app = FastAPI(title="DDoS Protection System", lifespan=lifespan)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Custom Rate Limit Handler that auto-blocks
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    client_ip = request.client.host if request.client else "0.0.0.0"
    if blocklist_manager.auto_block_enabled:
        await blocklist_manager.add_ip(client_ip, reason="Rate limit exceeded", banned_by="System")
        logger.warning(f"Auto-blocked IP {client_ip} due to rate limit")
    return _rate_limit_exceeded_handler(request, exc)

app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

@app.middleware("http")
async def blocklist_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "0.0.0.0"
    if blocklist_manager.is_blocked(client_ip):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=403, content={"detail": "IP is blocked."})
    return await call_next(request)

@app.get("/")
@limiter.limit(f"{settings.auto_block_threshold}/minute")
def root(request: Request):
    return {"message": "DDoS Protected Server is running!"}
