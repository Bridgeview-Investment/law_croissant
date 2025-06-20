class RegGenomeAPIError(Exception):
    """Base exception for RegGenome API errors"""
    pass

class AuthenticationError(RegGenomeAPIError):
    """Raised when authentication fails"""
    pass

class RateLimitError(RegGenomeAPIError):
    """Raised when rate limit is exceeded"""
    pass

class DataNotFoundError(RegGenomeAPIError):
    """Raised when requested data is not found"""
    pass

class ValidationError(RegGenomeAPIError):
    """Raised when request validation fails"""
    pass