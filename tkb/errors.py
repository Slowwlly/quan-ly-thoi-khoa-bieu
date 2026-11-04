class AppError(Exception):
    """Loi nghiep vu tra ve cho client dang JSON {"loi": ...}."""
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message, self.status = message, status


class Forbidden(AppError):
    def __init__(self, message='Ban khong co quyen thuc hien thao tac nay'):
        super().__init__(message, 403)


class NotFound(AppError):
    def __init__(self, message='Khong tim thay du lieu'):
        super().__init__(message, 404)


class Conflict(AppError):
    def __init__(self, message):
        super().__init__(message, 409)
