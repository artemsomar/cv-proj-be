from fastapi import APIRouter, Depends, HTTPException, status

from app.features.navigation.dependencies import get_navigation_service
from app.features.navigation.schemas import (
    NavigationInstructionsResponse,
    NavigationRouteRequest,
    NavigationRouteResponse,
    VerticesListResponse,
)
from app.features.navigation.service import NavigationService

router = APIRouter(prefix="/navigation", tags=["navigation"])


@router.get("/rooms", response_model=VerticesListResponse, status_code=status.HTTP_200_OK)
async def list_rooms(
    service: NavigationService = Depends(get_navigation_service),
) -> VerticesListResponse:
    try:
        return await service.list_vertices()
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/route", response_model=NavigationRouteResponse, status_code=status.HTTP_200_OK)
async def get_route(
    payload: NavigationRouteRequest,
    service: NavigationService = Depends(get_navigation_service),
) -> NavigationRouteResponse:
    try:
        return await service.build_route(payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/instructions", response_model=NavigationInstructionsResponse, status_code=status.HTTP_200_OK)
async def get_instructions(
    payload: NavigationRouteRequest,
    service: NavigationService = Depends(get_navigation_service),
) -> NavigationInstructionsResponse:
    try:
        return await service.build_instructions(payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
