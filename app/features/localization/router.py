from fastapi import APIRouter, Depends, File, UploadFile, status

from app.features.localization.dependencies import get_localization_service
from app.features.localization.schemas import LocalizationResponse
from app.features.localization.service import LocalizationService

router = APIRouter(prefix="/localization", tags=["localization"])


@router.post("/localize", response_model=LocalizationResponse, status_code=status.HTTP_200_OK)
async def localize_image(
    file: UploadFile = File(...),
    service: LocalizationService = Depends(get_localization_service),
) -> LocalizationResponse:
    return await service.localize_image(file)