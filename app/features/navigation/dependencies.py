from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db_session
from app.features.ai.client import GeminiClient
from app.features.ai.service import AIRouteNarrationService
from app.features.navigation.repository import NavigationRepository
from app.features.navigation.service import NavigationService


def get_navigation_service(db: AsyncSession = Depends(get_db_session)) -> NavigationService:
    settings = get_settings()
    repository = NavigationRepository(db=db)
    narrator = AIRouteNarrationService(
        client=GeminiClient(
            api_key=settings.google_api_key,
            model=settings.gemini_model,
        )
    )
    return NavigationService(repository=repository, narrator=narrator)
