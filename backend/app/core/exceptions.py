from fastapi import HTTPException, status


class AppException(HTTPException):
    """应用级异常基类"""
    def __init__(self, status_code: int, detail: str, error_code: str = None):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code


def not_found(detail: str = "资源不存在") -> AppException:
    return AppException(status_code=status.HTTP_404_NOT_FOUND, detail=detail, error_code="NOT_FOUND")


def unauthorized(detail: str = "未授权") -> AppException:
    return AppException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, error_code="UNAUTHORIZED")


def forbidden(detail: str = "无权限") -> AppException:
    return AppException(status_code=status.HTTP_403_FORBIDDEN, detail=detail, error_code="FORBIDDEN")


def bad_request(detail: str = "请求参数错误") -> AppException:
    return AppException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail, error_code="BAD_REQUEST")