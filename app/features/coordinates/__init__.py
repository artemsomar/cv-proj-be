from fastapi import APIRouter, UploadFile, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/coordinates", tags=["coordinates"])


@router.post(
    "/upload-image",
    status_code=status.HTTP_200_OK,
)
async def upload_image(file: UploadFile) -> JSONResponse:
    content = await file.read()

    return JSONResponse(
        content={
            "filename": file.filename,
            "content_type": file.content_type,
            "size_bytes": len(content),
            "message": "Image received. Processing to be implemented.",
        }
    )