from fastapi import APIRouter, HTTPException, status

from source.schemas.request import HypothesisRequest
from source.services.llm import get_llm_response


router = APIRouter(prefix="/api/v1/hypothesis", tags=["hypothesis"])

@router.post(
    path="/",
    summary="Сгенерировать новую гипотезу",
    status_code=status.HTTP_200_OK
)
async def generate_hypothesis(hypothesis: HypothesisRequest):
    try:
        response = get_llm_response(hypothesis.text)
        if not response:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Не удалось сгенирировать гипотезу")
        return {"status": "SUCCESS", "answer": response}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Не удалось сгенирировать гипотезу")