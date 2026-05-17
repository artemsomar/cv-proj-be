from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from .repository import ImportRepository
from .schemas import (
    BatchGraphResponse,
    BatchUpsertGraphRequest,
    EdgeResponse,
    PublishResponse,
    ValidateResponse,
    VertexResponse,
)


class ImportService:
    def __init__(self, db: AsyncSession, repository: ImportRepository) -> None:
        self.db = db
        self.repository = repository

    async def upload_graph(self, *, payload: BatchUpsertGraphRequest) -> BatchGraphResponse:
        version = await self.repository.get_draft_version()
        if version is None:
            name = f"draft-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
            version = await self.repository.create_version(name=name)
        else:
            await self.repository.clear_version_data(version_id=version.id)

        vertices = await self.repository.upsert_vertices(
            version_id=version.id, vertices=payload.vertices
        )
        edges = await self.repository.upsert_edges(
            version_id=version.id, edges=payload.edges
        )
        await self.db.commit()
        return BatchGraphResponse(
            vertices=[
                VertexResponse(
                    id=v.id,
                    floor=v.floor,
                    x=v.x,
                    y=v.y,
                    snap_radius=v.snap_radius,
                    metadata=v.props,
                )
                for v in vertices
            ],
            edges=[
                EdgeResponse(
                    id=e.id,
                    source=e.source,
                    target=e.target,
                    cost=e.cost,
                    reverse_cost=e.reverse_cost,
                    corridor_width=e.corridor_width,
                )
                for e in edges
            ],
        )

    async def validate(self) -> ValidateResponse:
        version = await self.repository.get_draft_version()
        if version is None:
            raise ValueError("No draft graph found. Upload a graph first.")
        errors = await self.repository.validate_version(version_id=version.id)
        return ValidateResponse(is_valid=not errors, errors=errors)

    async def publish(self) -> PublishResponse:
        version = await self.repository.get_draft_version()
        if version is None:
            raise ValueError("No draft graph found. Upload a graph first.")
        errors = await self.repository.validate_version(version_id=version.id)
        if errors:
            raise ValueError(f"Graph is invalid: {'; '.join(errors)}")
        await self.repository.publish_version(version_id=version.id)
        await self.db.commit()
        return PublishResponse(status="published")
