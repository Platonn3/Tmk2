import uvicorn
from fastapi import FastAPI
from source.api.v1.ingest import router as ingest_router
from source.api.v1.hypothesis import router as hypothesis_router
from db.populate_db import lifespan


# TODO: асинхронная обработка задач через celery
app = FastAPI(
    title="LLM API",
    lifespan=lifespan
)

app.include_router(ingest_router, prefix="/api/v1")
app.include_router(hypothesis_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(app)