import json

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import ValidationError

from .dependencies import get_import_service
from .schemas import BatchGraphResponse, PublishResponse, ValidateResponse, BatchUpsertGraphRequest
from .service import ImportService

router = APIRouter(prefix="/import", tags=["import"])


@router.post("/graph", response_model=BatchGraphResponse, status_code=status.HTTP_200_OK)
async def upload_graph(
    file: UploadFile,
    service: ImportService = Depends(get_import_service),
) -> BatchGraphResponse:
    try:
        raw = await file.read()
        data = json.loads(raw)
        payload = BatchUpsertGraphRequest.model_validate(data)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON file.") from error
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error.errors()) from error
    try:
        return await service.upload_graph(payload=payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/validate", response_model=ValidateResponse, status_code=status.HTTP_200_OK)
async def validate_graph(
    service: ImportService = Depends(get_import_service),
) -> ValidateResponse:
    try:
        return await service.validate()
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/publish", response_model=PublishResponse, status_code=status.HTTP_200_OK)
async def publish_graph(
    service: ImportService = Depends(get_import_service),
) -> PublishResponse:
    try:
        return await service.publish()
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
