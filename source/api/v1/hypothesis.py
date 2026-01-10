from fastapi import APIRouter, HTTPException, status


router = APIRouter(prefix="/api/v1/hypothesis", tags=["hypothesis"])

# TODO: ручку для генерации гипотез сделать
@router.post(
    path="/",
    summary="Сгенерировать новую гипотезу",
    status_code=status.HTTP_200_OK
)
async def generate_hypothesis():
    pass