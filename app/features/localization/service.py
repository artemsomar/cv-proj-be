import subprocess
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.features.localization.schemas import LocalizationResponse


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
TEMP_DIR = BASE_DIR / "temp_uploads"
TEMP_DIR.mkdir(exist_ok=True)

ACE_SCRIPT = BASE_DIR / "3d_localization" / "ace" / "ace_loc.py"
MODEL_PATH = BASE_DIR / "3d_loc_artifacts" / "floor_1_model" / "model_ff_stairs_v1_e_12.pt"
TRANSFORM_PATH = BASE_DIR / "3d_loc_artifacts" / "floor_1_model" / "transform.txt"
TRANSFORM_2D_PATH = BASE_DIR / "3d_loc_artifacts" / "floor_1_model" / "transform_2d.txt"
OUTPUT_FILE = BASE_DIR / "3d_localization" / "ace" / "camera_floorplan_coords.txt"


class LocalizationService:
    async def localize_image(self, file: UploadFile) -> LocalizationResponse:
        temp_filename = f"{uuid.uuid4()}.jpg"
        temp_path = TEMP_DIR / temp_filename

        try:
            content = await file.read()
            with open(temp_path, "wb") as f:
                f.write(content)

            cmd = [
                "python",
                str(ACE_SCRIPT),
                "--image", str(temp_path),
                "--model", str(MODEL_PATH),
                "--transform", str(TRANSFORM_PATH),
                "--transform-2d", str(TRANSFORM_2D_PATH),
                "--output", str(OUTPUT_FILE)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                return LocalizationResponse(
                    x=0, y=0, success=False,
                    message=f"Localization failed: {result.stderr}"
                )

            if not OUTPUT_FILE.exists():
                return LocalizationResponse(
                    x=0, y=0, success=False,
                    message="Output file not created"
                )

            with open(OUTPUT_FILE, "r") as f:
                lines = f.readlines()

            x, y = 0.0, 0.0
            for line in lines:
                if line.startswith("x="):
                    x = float(line.split("=")[1].strip().strip("[]"))
                elif line.startswith("y="):
                    y = float(line.split("=")[1].strip().strip("[]"))

            return LocalizationResponse(x=x, y=y, success=True)

        except subprocess.TimeoutExpired:
            return LocalizationResponse(
                x=0, y=0, success=False,
                message="Localization timed out"
            )
        except Exception as e:
            return LocalizationResponse(
                x=0, y=0, success=False,
                message=str(e)
            )
        finally:
            if temp_path.exists():
                temp_path.unlink()