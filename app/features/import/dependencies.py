from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from .repository import ImportRepository
from .service import ImportService


def get_import_service(db: AsyncSession = Depends(get_db_session)) -> ImportService:
    return ImportService(db=db, repository=ImportRepository(db=db))
