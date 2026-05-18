import subprocess
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.features.localization.schemas import LocalizationResponse, MultiFloorLocalizationResponse


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
TEMP_DIR = BASE_DIR / "temp_uploads"
TEMP_DIR.mkdir(exist_ok=True)

ACE_SCRIPT = BASE_DIR / "3d_localization" / "ace" / "ace_loc.py"

FLOOR_MODELS = {
    "floor_1": {
        "model_path": BASE_DIR / "3d_loc_artifacts" / "floor_1_model" / "model_ff_stairs_v1_e_12.pt",
        "transform_path": BASE_DIR / "3d_loc_artifacts" / "floor_1_model" / "transform.txt",
        "transform_2d_path": BASE_DIR / "3d_loc_artifacts" / "floor_1_model" / "transform_2d.txt",
    },
    "floor_2": {
        "model_path": BASE_DIR / "3d_loc_artifacts" / "floor_2_model" / "model_sf_stairs.pt",
        "transform_path": BASE_DIR / "3d_loc_artifacts" / "floor_2_model" / "transform.txt",
        "transform_2d_path": BASE_DIR / "3d_loc_artifacts" / "floor_2_model" / "transform_2d.txt",
    },
}

OUTPUT_FILE = BASE_DIR / "3d_localization" / "ace" / "camera_floorplan_coords.txt"


class LocalizationService:
    async def localize_image(self, file: UploadFile) -> MultiFloorLocalizationResponse:
        """
        Localize image across all available floors.

        Args:
            file: Uploaded image file

        Returns:
            MultiFloorLocalizationResponse with current (best by inliers) and results for all floors
        """
        results = []
        file_content = await file.read()

        for floor in FLOOR_MODELS:
            result = await self._localize_on_floor(file_content, floor)
            results.append(result)

        best_result = max(results, key=lambda r: r.inliers if r.success else -1)

        return MultiFloorLocalizationResponse(current=best_result, results=results)

    async def _localize_on_floor(self, file_content: bytes, floor: str) -> LocalizationResponse:
        floor_config = FLOOR_MODELS[floor]
        temp_filename = f"{uuid.uuid4()}.jpg"
        temp_path = TEMP_DIR / temp_filename
        output_file = TEMP_DIR / f"output_{floor}_{uuid.uuid4()}.txt"

        try:
            with open(temp_path, "wb") as f:
                f.write(file_content)

            cmd = [
                "python",
                str(ACE_SCRIPT),
                "--image", str(temp_path),
                "--model", str(floor_config["model_path"]),
                "--transform", str(floor_config["transform_path"]),
                "--transform-2d", str(floor_config["transform_2d_path"]),
                "--output", str(output_file),
                "--floor", floor
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                return LocalizationResponse(
                    x=0, y=0, success=False, floor=floor,
                    message=f"Localization failed: {result.stderr}"
                )

            if not output_file.exists():
                return LocalizationResponse(
                    x=0, y=0, success=False, floor=floor,
                    message="Output file not created"
                )

            with open(output_file, "r") as f:
                lines = f.readlines()

            x, y = 0.0, 0.0
            inliers = 0
            detected_floor = floor
            for line in lines:
                if line.startswith("x="):
                    x = float(line.split("=")[1].strip().strip("[]"))
                elif line.startswith("y="):
                    y = float(line.split("=")[1].strip().strip("[]"))
                elif line.startswith("inliers="):
                    inliers = int(line.split("=")[1].strip().strip("[]"))
                elif line.startswith("floor="):
                    detected_floor = line.split("=")[1].strip().strip("[]")

            return LocalizationResponse(x=x, y=y, success=True, inliers=inliers, floor=detected_floor)

        except subprocess.TimeoutExpired:
            return LocalizationResponse(
                x=0, y=0, success=False, floor=floor,
                message="Localization timed out"
            )
        except Exception as e:
            return LocalizationResponse(
                x=0, y=0, success=False, floor=floor,
                message=str(e)
            )
        finally:
            if temp_path.exists():
                temp_path.unlink()
            if output_file.exists():
                output_file.unlink()