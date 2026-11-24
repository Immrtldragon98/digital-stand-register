from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config.settings import settings
import app.models  # noqa: F401 - registers SQLAlchemy models
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(GZipMiddleware, minimum_size=700)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root_health():
    return {"status": "healthy", "system": "Digital Stand Register API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get('/ready')
def readiness():
    from sqlalchemy import text
    from app.database.session import engine
    from fastapi.responses import JSONResponse
    try:
        with engine.connect() as connection:
            connection.execute(text('SELECT 1'))
        return {'status':'ready','database':'reachable'}
    except Exception:
        return JSONResponse(status_code=503,content={'status':'unavailable','database':'unreachable'})


@app.middleware('http')
async def request_diagnostics(request, call_next):
    import logging
    import time
    import uuid
    from fastapi.responses import JSONResponse
    request_id = uuid.uuid4().hex
    started = time.monotonic()
    logger = logging.getLogger('dsr.requests')
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error('request_id=%s method=%s path=%s exception=%s', request_id,request.method,request.url.path,type(exc).__name__)
        response = JSONResponse(status_code=500,content={'detail':'Request failed. Check current state before retrying.','request_id':request_id})
    response.headers['X-Request-ID'] = request_id
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    logger.info('request_id=%s method=%s path=%s status=%s elapsed_ms=%.1f',request_id,request.method,request.url.path,response.status_code,(time.monotonic()-started)*1000)
    return response
