"""
Telex FastAPI application entry point.
"""
import asyncio
import os
import re
import uuid
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import auth, repos, packages, webhooks, stats, settings as settings_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("telex.api")


# ── Security: redact API key patterns from all log output ───────────────────
_KEY_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}"
    r"|AIza[A-Za-z0-9_\-]{30,}"
    r"|sk-ant-[A-Za-z0-9_\-]{20,}"
    r"|[A-Za-z0-9]{40,})"
)


class _RedactKeysFilter(logging.Filter):
    """Strip likely API key strings from all log records before emission."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        record.msg = _KEY_PATTERN.sub("[REDACTED]", str(record.msg))
        if record.args:
            try:
                record.args = tuple(
                    _KEY_PATTERN.sub("[REDACTED]", str(a)) if isinstance(a, str) else a
                    for a in (record.args if isinstance(record.args, tuple) else (record.args,))
                )
            except Exception:
                pass
        return True


logging.root.addFilter(_RedactKeysFilter())
# ───────────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Telex API starting up — LLM provider: %s", settings.llm_provider_default)
    # Start embedded worker loop for free single-service hosting
    worker_task = None
    scheduler = None
    if os.getenv("EMBEDDED_WORKER", "true").lower() in ("true", "1", "yes"):
        try:
            from jobs.worker import worker_loop, start_scheduler
            scheduler = start_scheduler()
            worker_task = asyncio.create_task(worker_loop(f"worker-embedded-{uuid.uuid4().hex[:6]}"))
            logger.info("Embedded autonomous job worker started in background.")
        except Exception as e:
            logger.warning("Could not start embedded background worker: %s", e)

    yield

    if worker_task:
        worker_task.cancel()
    if scheduler:
        try:
            scheduler.shutdown()
        except Exception:
            pass
    logger.info("Telex API shutting down")


app = FastAPI(
    title="Telex API",
    description="Self-healing API dependency bot",
    version="0.1.0",
    lifespan=lifespan,
)

_is_prod = bool(os.getenv("RENDER") or os.getenv("ENVIRONMENT", "").lower() == "production")

# CORS — allow explicitly configured origins, local dev, and project-specific Vercel preview deploys
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^https://(telex|aura-drops)[a-zA-Z0-9_-]*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers
app.include_router(auth.router)
app.include_router(auth.router, prefix="/api")
app.include_router(repos.router)
app.include_router(packages.router)
app.include_router(webhooks.router)
app.include_router(stats.router)
app.include_router(settings_router.router)



@app.get("/health")
async def health():
    return {"status": "ok", "provider": settings.llm_provider_default}


from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Global exception handler caught: %s on %s", exc, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )
