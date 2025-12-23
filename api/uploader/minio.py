import os

import filetype
from fastapi import UploadFile, File as UploadFileParam, Depends, HTTPException, APIRouter

from core.deps import get_current_user_id
from models.schemas.file import FileUploadDTO
from services.minio_service import minio_service
from utils.response import APIResponse

minio_router = APIRouter(prefix='/minio')


@minio_router.post("/upload")
async def upload(
        file: UploadFile = UploadFileParam(..., description="上传的文件"),
        dto: FileUploadDTO = Depends(FileUploadDTO),
        user_id: int = Depends(get_current_user_id)
):
    """
    上传文件
    :param user_id: 登录用户id
    :param file: 上传的文件
    :param dto: 文件上传DTO
    :return: 文件VO
    """
    data = await file.read()
    if file.size != len(data):
        raise HTTPException(status_code=400, detail="提供的文件大小与实际大小不匹配")

    # 文件真实类型校验
    kind = filetype.guess(data)
    if kind is None:
        raise HTTPException(status_code=400, detail="无法识别文件类型")

    # 检查扩展名是否匹配
    ext = os.path.splitext(file.filename)[1].lower().strip('.')
    if ext != kind.extension:
        # 特殊处理：jpeg 和 jpg 视为相同
        if not (ext in ['jpg', 'jpeg', 'png'] and kind.extension in ['jpg', 'jpeg', 'png']):
            raise HTTPException(status_code=400,
                                detail=f"文件扩展名与实际类型不匹配: 预期 {kind.extension}, 实际 {ext}")

    file_type = file.filename.split('.')[-1]
    vo = await minio_service.upload_file_and_record(dto, user_id, file_type, file.size, file.filename, data)
    return APIResponse.success(vo)
