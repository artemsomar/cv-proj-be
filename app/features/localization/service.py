import io
import torch
import numpy as np
from PIL import Image, ImageOps

# Pillow resampling compatibility
try:
    RESAMPLE_LANCZOS = Image.Resampling.LANCZOS
except Exception:
    RESAMPLE_LANCZOS = Image.LANCZOS
from pathlib import Path

from fastapi import UploadFile
import torchvision.transforms.functional as TF
import cv2

from app.features.localization.schemas import LocalizationResponse, MultiFloorLocalizationResponse


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

sys_path = str(BASE_DIR / "3d_localization" / "ace")
import sys
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from ace_network import Regressor


class FloorModel:
    def __init__(self, floor_name: str, model_path: Path, transform_path: Path, transform_2d_path: Path):
        self.floor_name = floor_name
        self.model_path = model_path
        self.transform_path = transform_path
        self.transform_2d_path = transform_2d_path
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.regressor = None
        self.transform_3d = None
        self.transform_2d = None
        self._load_model()

    def _load_model(self):
        mean = torch.tensor([0.485, 0.456, 0.406])
        std = torch.tensor([0.229, 0.224, 0.225])

        self.regressor = Regressor(
            num_head_blocks=1,
            use_homogeneous=True,
            mean=mean
        )

        encoder_path = BASE_DIR / "3d_localization" / "ace" / "ace_encoder_pretrained.pt"
        self.regressor.encoder.load_state_dict(torch.load(encoder_path, map_location=self.device))

        state_dict = torch.load(self.model_path, map_location=self.device)
        fixed_head_state_dict = {f"heads.{k}": v for k, v in state_dict.items()}
        self.regressor.load_state_dict(fixed_head_state_dict, strict=False)
        self.regressor = self.regressor.to(self.device)
        self.regressor.eval()

        if self.transform_path.exists():
            self.transform_3d = np.loadtxt(self.transform_path)

        if self.transform_2d_path.exists():
            self.transform_2d = self._load_2d_transform(self.transform_2d_path)

    def _load_2d_transform(self, filepath):
        params = {}
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    try:
                        key, val = line.split('=', 1)
                        params[key.strip()] = float(val.strip())
                    except:
                        pass

        return {
            'scale_x': params.get('scale_x', 1.0),
            'scale_y': params.get('scale_y', 1.0),
            'rotation_deg': params.get('rotation_deg', 0.0),
            'tx': params.get('tx', 0.0),
            'ty': params.get('ty', 0.0),
            'original_image_width': params.get('original_image_width', 3277),
            'original_image_height': params.get('original_image_height', 919),
            'output_width': params.get('output_width', 700),
            'output_height': params.get('output_height', 200),
        }

    def localize(self, image_bytes: bytes) -> LocalizationResponse:
        try:
            # Load image and apply EXIF orientation if present so the
            # image matches the photographer's intended orientation.
            img = Image.open(io.BytesIO(image_bytes))
            img = ImageOps.exif_transpose(img)
            img = img.convert('L')
            print("img size:", img.size)

            orig_w, orig_h = img.size
            target_h = 480
            target_w = int(orig_w * (target_h / orig_h))
            img_resized = img.resize((target_w, target_h), RESAMPLE_LANCZOS)

            input_tensor = TF.to_tensor(img_resized).unsqueeze(0).to(self.device)
            mean = torch.tensor([0.449]).view(1, 1, 1, 1).to(self.device)
            std = torch.tensor([0.226]).view(1, 1, 1, 1).to(self.device)
            input_tensor = (input_tensor - mean) / std

            with torch.no_grad():
                scene_coords = self.regressor(input_tensor)

            _, _, h_feat, w_feat = scene_coords.shape
            y, x = torch.meshgrid(torch.arange(h_feat), torch.arange(w_feat), indexing='ij')

            points2D = torch.stack(((x + 0.5) * 8 * (orig_w / target_w),
                                    (y + 0.5) * 8 * (orig_h / target_h)), dim=-1).cpu().numpy().reshape(-1, 2)

            points3D = scene_coords.squeeze().permute(1, 2, 0).cpu().numpy().reshape(-1, 3)

            focal_px = 0.8 * max(orig_w, orig_h)
            camera_matrix = np.array([
                [focal_px, 0, orig_w / 2],
                [0, focal_px, orig_h / 2],
                [0, 0, 1]
            ], dtype=np.float64)
            dist_coeffs = np.zeros((4, 1), dtype=np.float64)

            obj_pts = np.ascontiguousarray(points3D, dtype=np.float32)
            img_pts = np.ascontiguousarray(points2D, dtype=np.float32)

            success, rvec, tvec, inliers = cv2.solvePnPRansac(
                obj_pts, img_pts, camera_matrix, dist_coeffs,
                reprojectionError=30.0, iterationsCount=5000,
                confidence=0.9, flags=cv2.SOLVEPNP_SQPNP
            )

            if not success or inliers is None or len(inliers) < 20:
                return LocalizationResponse(x=0, y=0, success=False, floor=self.floor_name, message="Localization failed")

            num_inliers = len(inliers)
            R_w2c, _ = cv2.Rodrigues(rvec)
            t_w2c = tvec.reshape(3, 1)
            camera_center = -np.dot(R_w2c.T, t_w2c)

            ace_training_mean = np.array([0.04, -0.03, 0.05]).reshape(3, 1)
            camera_center += ace_training_mean

            if self.transform_3d is not None:
                C = camera_center
                C_new = self.transform_3d[:3, :3] @ C + self.transform_3d[:3, 3].reshape(3, 1)
                camera_center = C_new.ravel()

            if self.transform_2d:
                x_floor, y_floor = self._coords_to_floorplan(camera_center[0], camera_center[1], self.transform_2d)
            else:
                x_floor, y_floor = camera_center[0], camera_center[1]

            return LocalizationResponse(x=float(x_floor), y=float(y_floor), success=True, inliers=num_inliers, floor=self.floor_name)

        except Exception as e:
            return LocalizationResponse(x=0, y=0, success=False, floor=self.floor_name, message=str(e))

    def _coords_to_floorplan(self, world_x, world_y, transform):
        orig_w = transform.get('original_image_width', 3277)
        orig_h = transform.get('original_image_height', 919)
        out_w = transform.get('output_width', 700)
        out_h = transform.get('output_height', 200)

        scale_x = transform['scale_x'] * (out_w / orig_w)
        scale_y = transform['scale_y'] * (out_h / orig_h)
        tx = transform['tx'] * (out_w / orig_w)
        ty = transform['ty'] * (out_h / orig_h)
        rotation = transform['rotation_deg']

        x = world_x * scale_x
        y = world_y * scale_y

        angle_rad = np.radians(rotation)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)
        x_rot = x * cos_a - y * sin_a
        y_rot = x * sin_a + y * cos_a

        x_img = x_rot + tx
        y_img = y_rot + ty

        x_floor = x_img
        y_floor = out_h - y_img

        return x_floor, y_floor


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


class LocalizationService:
    def __init__(self):
        self.floor_models: dict[str, FloorModel] = {}
        self._load_all_floors()

    def _load_all_floors(self):
        for floor_name, config in FLOOR_MODELS.items():
            self.floor_models[floor_name] = FloorModel(
                floor_name=floor_name,
                model_path=config["model_path"],
                transform_path=config["transform_path"],
                transform_2d_path=config["transform_2d_path"],
            )

    async def localize_image(self, file: UploadFile) -> MultiFloorLocalizationResponse:
        file_content = await file.read()

        results = []
        for floor_name, floor_model in self.floor_models.items():
            result = floor_model.localize(file_content)
            results.append(result)

        best_result = max(results, key=lambda r: r.inliers if r.success else -1)

        return MultiFloorLocalizationResponse(current=best_result, results=results)