"""Custom exception classes for API."""


class APIException(Exception):
    """Base exception for API errors."""
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class FileNotFoundError(APIException):
    """Exception raised when a file is not found."""
    
    def __init__(self, filename: str):
        message = f"File not found: {filename}"
        super().__init__(message, status_code=404)
        self.filename = filename


class ValidationError(APIException):
    """Exception raised when validation fails."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class ProcessingError(APIException):
    """Exception raised when data processing fails."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class SecurityError(APIException):
    """Exception raised when security validation fails."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

