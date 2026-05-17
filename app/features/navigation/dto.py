from dataclasses import dataclass


@dataclass(slots=True)
class VertexDTO:
    id: int
    floor: int
    x: float
    y: float
    snap_radius: float
