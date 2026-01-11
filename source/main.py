import uvicorn
from fastapi import FastAPI
from source.api.v1.ingest import router as ingest_router
from source.api.v1.hypothesis import router as hypothesis_router

from celery import Celery

# TODO: асинхронная обработка задач через celery
app = FastAPI(
    title="LLM API"
)

celery_app = Celery('articles', broker='redis://redis:6379/0',  backend='redis://redis:6379/0')

app.include_router(ingest_router, prefix="/api/v1")
app.include_router(hypothesis_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(app)