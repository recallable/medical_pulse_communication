from crud.base import BaseCRUD
from models.entity.file import File

class CRUDFile(BaseCRUD[File]):
    pass

file_crud = CRUDFile(File)
