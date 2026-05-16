from pydantic import BaseModel


class LocalizationResponse(BaseModel):
    x: float
    y: float
    success: bool
    message: str = ""
    inliers: int = 0
    floor: str = "floor_1"
