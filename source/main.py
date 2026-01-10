import uvicorn
from fastapi import FastAPI
from source.api.v1.ingest import router as ingest_router

# TODO: асинхронная обработка задач через celery
app = FastAPI(
    title="LLM API"
)
app.include_router(ingest_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(app)