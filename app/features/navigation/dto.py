from dataclasses import dataclass


@dataclass(slots=True)
class VertexDTO:
    id: int
    name: str | None
    type: str | None
    floor: int
    x: float
    y: float
    snap_radius: float
