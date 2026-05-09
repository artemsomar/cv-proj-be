from dataclasses import dataclass


@dataclass(slots=True)
class RouteNarrationInput:
    heading_degrees: float
    total_distance: float
    vertices: list[dict]
    segments: list[dict]
