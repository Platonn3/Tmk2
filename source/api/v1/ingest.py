from fastapi import APIRouter, status, HTTPException
from starlette.concurrency import run_in_threadpool

from source.schemas.request import ArticleDownload
from source.services.downloader import Downloader


router = APIRouter(prefix="/article", tags=["articles"])


@router.post(
    "/",
    summary="Скачать статью по ссылке",
    status_code=status.HTTP_201_CREATED
)
async def download_article(data: ArticleDownload):
    downloader = Downloader()
    try:
        success = await run_in_threadpool(downloader.process, str(data.url))
        if not success:
            raise HTTPException(status_code=404, detail="Не удалось найти PDF по этой ссылке")
        return {"status": "SUCCESS"}
    except Exception:
        raise HTTPException(status_code=500, detail="При скачивании статьи произошла ошибка")

