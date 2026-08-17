from fastapi import FastAPI
from app.api.router import router



app = FastAPI()



app.include_router(router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "Hello World"}

