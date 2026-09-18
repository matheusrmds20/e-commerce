from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.exceptions import register_exception_handlers
from app.api.router import router



app = FastAPI()

# CORS — libera o dev server do Vite (e o preview) para chamar a API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Handlers globais: converte exceções da app em { error: { code, message } }
register_exception_handlers(app)


app.include_router(router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "Hello World"}

