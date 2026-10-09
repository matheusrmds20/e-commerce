from celery import Celery
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.exceptions import register_exception_handlers
from app.api.limiter import limiter
from app.api.router import router
from app.core.config import get_settings

app = FastAPI()

# Rate limiting (slowapi): instância global usada pelos @limiter.limit(...)
# das rotas. Obrigatório setar app.state.limiter para o slowapi funcionar;
# o handler de 429 é registrado dentro de register_exception_handlers().
app.state.limiter = limiter



celery = Celery(
    "ecommerce",
    broker=get_settings().CELERY_BROKER_URL,
    backend=get_settings().CELERY_RESULT_BACKEND,

)

celery.conf.imports = ("app.utils.email", "app.utils.receipt_tasks")







app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


register_exception_handlers(app)


app.include_router(router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "Hello World"}

