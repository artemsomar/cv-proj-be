from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .repository import ImportRepository
from .schemas import (
    BatchEdgesResponse,
    BatchUpsertEdgesRequest,
    BatchUpsertVerticesRequest,
    BatchVerticesResponse,
    EdgeResponse,
    GraphVersionResponse,
    PublishResponse,
    ValidateResponse,
    VertexResponse,
)


class DuplicateGraphVersionNameError(ValueError):
    pass


class ImportService:
    def __init__(self, db: AsyncSession, repository: ImportRepository) -> None:
        self.db = db
        self.repository = repository

    async def create_version(self, *, name: str) -> GraphVersionResponse:
        try:
            version = await self.repository.create_version(name=name)
            await self.db.commit()
        except IntegrityError as error:
            await self.db.rollback()
            raise DuplicateGraphVersionNameError(
                f"Graph version with name '{name}' already exists."
            ) from error
        return GraphVersionResponse(id=version.id, name=version.name, status=version.status)

    async def clone_version(self, *, version_id: int, name: str) -> GraphVersionResponse:
        source = await self.repository.get_version(version_id=version_id)
        if source is None:
            raise ValueError("Source version not found.")
        try:
            clone = await self.repository.clone_version(source=source, cloned_name=name)
            await self.db.commit()
        except IntegrityError as error:
            await self.db.rollback()
            raise DuplicateGraphVersionNameError(
                f"Graph version with name '{name}' already exists."
            ) from error
        return GraphVersionResponse(id=clone.id, name=clone.name, status=clone.status)

    async def upsert_vertices(
        self, *, version_id: int, payload: BatchUpsertVerticesRequest
    ) -> BatchVerticesResponse:
        version = await self.repository.get_version(version_id=version_id)
        if version is None:
            raise ValueError("Version not found.")
        if version.status != "draft":
            raise ValueError("Only draft versions can be edited.")
        vertices = await self.repository.upsert_vertices(
            version_id=version_id, vertices=payload.vertices
        )
        await self.db.commit()
        return BatchVerticesResponse(
            vertices=[
                VertexResponse(
                    id=vertex.id,
                    floor=vertex.floor,
                    x=vertex.x,
                    y=vertex.y,
                    snap_radius=vertex.snap_radius,
                    metadata=vertex.props,
                )
                for vertex in vertices
            ]
        )

    async def upsert_edges(
        self, *, version_id: int, payload: BatchUpsertEdgesRequest
    ) -> BatchEdgesResponse:
        version = await self.repository.get_version(version_id=version_id)
        if version is None:
            raise ValueError("Version not found.")
        if version.status != "draft":
            raise ValueError("Only draft versions can be edited.")
        edges = await self.repository.upsert_edges(version_id=version_id, edges=payload.edges)
        await self.db.commit()
        return BatchEdgesResponse(
            edges=[
                EdgeResponse(
                    id=edge.id,
                    source=edge.source,
                    target=edge.target,
                    cost=edge.cost,
                    reverse_cost=edge.reverse_cost,
                    corridor_width=edge.corridor_width,
                )
                for edge in edges
            ]
        )

    async def validate(self, *, version_id: int) -> ValidateResponse:
        version = await self.repository.get_version(version_id=version_id)
        if version is None:
            raise ValueError("Version not found.")
        errors = await self.repository.validate_version(version_id=version_id)
        return ValidateResponse(is_valid=not errors, errors=errors)

    async def publish(self, *, version_id: int) -> PublishResponse:
        version = await self.repository.get_version(version_id=version_id)
        if version is None:
            raise ValueError("Version not found.")
        errors = await self.repository.validate_version(version_id=version_id)
        if errors:
            raise ValueError(f"Version is invalid: {'; '.join(errors)}")
        await self.repository.publish_version(version_id=version_id)
        await self.db.commit()
        return PublishResponse(version_id=version_id, status="published")
