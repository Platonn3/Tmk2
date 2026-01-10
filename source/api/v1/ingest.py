from fastapi import APIRouter, status, HTTPException
from starlette.concurrency import run_in_threadpool

from source.schemas.request import ArticleDownload
from source.services.downloader import Downloader

from db.populate_db import add_single_document_to_db


router = APIRouter(prefix="/article", tags=["articles"])


@router.post(
    "/",
    summary="Добавить статью по ссылке в базу данных",
    status_code=status.HTTP_200_OK
)
async def download_article(data: ArticleDownload) -> dict:
    downloader = Downloader()
    try:
        success = downloader.process(str(data.url))
        if not success:
            raise HTTPException(status_code=404, detail="Не удалось найти PDF по этой ссылке")

        add_single_document_to_db("../data_sources/scraped_article.pdf")

        return {"status": "SUCCESS"}
    except Exception:
        raise HTTPException(status_code=500, detail="При скачивании статьи произошла ошибка")