from typing import Optional

from pydantic import BaseModel, Field


class FileUploadDTO(BaseModel):
    module: int = Field(..., description="业务模块名称")


class FileVO(BaseModel):
    id: int = Field(..., description="文件ID")
    bucket: str = Field(..., description="存储桶名称")
    file_name: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")


class OCRVo(BaseModel):
    name: str = Field(..., description="姓名")
    id_card: str = Field(..., description="身份证")
    file_id: int


class OCRResponse(BaseModel):
    code: int = Field(..., description="状态码")
    message: str = Field(..., description="返回信息")
    data: Optional[OCRVo] = Field(..., description="返回数据")
