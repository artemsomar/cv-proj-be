from pydantic import BaseModel, Field


class VertexUpsertItem(BaseModel):
    id: int
    name: str | None = None
    type: str | None = None
    floor: int = Field(ge=0)
    x: float
    y: float
    snap_radius: float = Field(default=1.0, gt=0)


class EdgeUpsertItem(BaseModel):
    id: int
    source: int
    target: int
    cost: float = Field(ge=0)
    reverse_cost: float = Field(ge=0)
    corridor_width: float = Field(default=1.0, gt=0)


class VertexResponse(BaseModel):
    id: int
    name: str | None
    type: str | None
    floor: int
    x: float
    y: float
    snap_radius: float


class EdgeResponse(BaseModel):
    id: int
    source: int
    target: int
    cost: float
    reverse_cost: float
    corridor_width: float


class BatchUpsertGraphRequest(BaseModel):
    vertices: list[VertexUpsertItem]
    edges: list[EdgeUpsertItem]


class BatchGraphResponse(BaseModel):
    vertices: list[VertexResponse]
    edges: list[EdgeResponse]


class ValidateResponse(BaseModel):
    is_valid: bool
    errors: list[str]


class PublishResponse(BaseModel):
    status: str
