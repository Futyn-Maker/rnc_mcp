class RNCError(Exception):
    """Base exception for all RNC MCP errors."""
    pass


class RNCConfigError(RNCError):
    """Raised when configuration is missing or invalid."""
    pass


class RNCAuthError(RNCError):
    """Raised when authentication fails (invalid token)."""
    pass


class RNCAPIError(RNCError):
    """Raised when the RNC API returns an error response."""
    pass
