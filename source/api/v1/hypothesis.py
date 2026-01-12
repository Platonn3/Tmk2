from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, status

from source.schemas.request import HypothesisRequest
from source.services.llm import get_llm_response

from source.services.celery_app import celery_app



router = APIRouter(prefix="/hypothesis", tags=["hypothesis"])

@router.post(
    path="/",
    summary="Сгенерировать новую гипотезу",
    status_code=status.HTTP_200_OK
)
async def generate_hypothesis(hypothesis: HypothesisRequest):
    try:
        task = get_llm_response.delay(hypothesis.text)
        return {"task_id": task.id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Не удалось сгенирировать гипотезу, произошла ошибка: {e}")


@router.get(
    "/{task_id}",
    summary="Получить результат выполнения задачи",
    status_code=status.HTTP_200_OK
)
async def get_task_result(task_id: str):
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        if task_result.state == "SUCCESS":
            response = task_result.result
            if not response:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Не удалось сгенирировать гипотезу")
            return {"status": "SUCCESS", "answer": response}
        return  {"status": task_result.state}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Не удалось сгенирировать гипотезу, произошла ошибка: {e}")
