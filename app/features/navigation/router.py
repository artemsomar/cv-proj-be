from fastapi import APIRouter, Depends, HTTPException, status

from app.features.navigation.dependencies import get_navigation_service
from app.features.navigation.schemas import NavigationRouteRequest, NavigationRouteResponse
from app.features.navigation.service import NavigationService

router = APIRouter(prefix="/navigation", tags=["navigation"])


@router.post("/route", response_model=NavigationRouteResponse, status_code=status.HTTP_200_OK)
async def get_route(
    payload: NavigationRouteRequest,
    service: NavigationService = Depends(get_navigation_service),
) -> NavigationRouteResponse:
    try:
        return await service.build_route(payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
