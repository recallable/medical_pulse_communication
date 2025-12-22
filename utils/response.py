class APIResponse:
    def __init__(self, code=200, message="success", data=None):
        self.code = code
        self.message = message
        self.data = data
        
    @staticmethod
    def success(data=None, message="success", code=200):
        return {"code": code, "message": message, "data": data}

    @staticmethod
    def error(message="error", code=400, data=None):
        return {"code": code, "message": message, "data": data}

    @staticmethod
    def page(items, total, page, size, message="success", code=200):
        return {"code": code, "message": message, "data": {"items": items, "total": total, "page": page, "size": size}}