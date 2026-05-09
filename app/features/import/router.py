from fastapi import APIRouter, Depends, HTTPException, status

from .dependencies import get_import_service
from .schemas import (
    BatchEdgesResponse,
    BatchUpsertEdgesRequest,
    BatchUpsertVerticesRequest,
    BatchVerticesResponse,
    GraphVersionCreateRequest,
    GraphVersionResponse,
    PublishResponse,
    ValidateResponse,
)
from .service import DuplicateGraphVersionNameError, ImportService

router = APIRouter(prefix="/import", tags=["import"])


@router.post("/versions", response_model=GraphVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_graph_version(
    payload: GraphVersionCreateRequest,
    service: ImportService = Depends(get_import_service),
) -> GraphVersionResponse:
    try:
        return await service.create_version(name=payload.name)
    except DuplicateGraphVersionNameError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post(
    "/versions/{version_id}/clone",
    response_model=GraphVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def clone_graph_version(
    version_id: int,
    payload: GraphVersionCreateRequest,
    service: ImportService = Depends(get_import_service),
) -> GraphVersionResponse:
    try:
        return await service.clone_version(version_id=version_id, name=payload.name)
    except DuplicateGraphVersionNameError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post(
    "/versions/{version_id}/vertices:batch-upsert",
    response_model=BatchVerticesResponse,
    status_code=status.HTTP_200_OK,
)
async def upsert_vertices(
    version_id: int,
    payload: BatchUpsertVerticesRequest,
    service: ImportService = Depends(get_import_service),
) -> BatchVerticesResponse:
    try:
        return await service.upsert_vertices(version_id=version_id, payload=payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post(
    "/versions/{version_id}/edges:batch-upsert",
    response_model=BatchEdgesResponse,
    status_code=status.HTTP_200_OK,
)
async def upsert_edges(
    version_id: int,
    payload: BatchUpsertEdgesRequest,
    service: ImportService = Depends(get_import_service),
) -> BatchEdgesResponse:
    try:
        return await service.upsert_edges(version_id=version_id, payload=payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/versions/{version_id}/validate", response_model=ValidateResponse)
async def validate_version(
    version_id: int,
    service: ImportService = Depends(get_import_service),
) -> ValidateResponse:
    try:
        return await service.validate(version_id=version_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/versions/{version_id}/publish", response_model=PublishResponse)
async def publish_version(
    version_id: int,
    service: ImportService = Depends(get_import_service),
) -> PublishResponse:
    try:
        return await service.publish(version_id=version_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
