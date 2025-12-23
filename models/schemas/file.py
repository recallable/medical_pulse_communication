from pydantic import BaseModel, Field


class FileUploadDTO(BaseModel):
    module: int = Field(..., description="业务模块名称")

class FileVO(BaseModel):
    id: int = Field(..., description="文件ID")
    bucket: str = Field(..., description="存储桶名称")
    file_name: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")
