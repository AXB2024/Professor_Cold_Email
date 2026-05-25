import logging
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.routes.analytics_routes import router as analytics_router
from app.routes.email_routes import router as email_router
from app.routes.resume_routes import router as resume_router

settings = get_settings()
setup_logging(settings)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Backend service for generating and sending personalized professor outreach emails.",
)

# Swagger UI is automatically available at /docs.
# To test POST /generate_emails there:
# 1) Open /docs
# 2) Expand POST /generate_emails
# 3) Click "Try it out", paste JSON body, then Execute.
app.include_router(email_router)
app.include_router(resume_router)
app.include_router(analytics_router)

# Keep origins explicit for local development.
# Avoid allow_origins=["*"] in production deployments.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "request method=%s path=%s status=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("validation_error path=%s errors=%s", request.url.path, exc.errors())
    return JSONResponse(
        status_code=422,
        content={
            "error": "Invalid or missing request body.",
            "details": exc.errors(),
            "hint": "Use POST /generate_emails with 'student' and 'professors' fields.",
        },
    )


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "API is running",
        "docs": "/docs",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
