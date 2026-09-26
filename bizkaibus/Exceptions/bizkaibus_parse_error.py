from .bizkaibus_error import BizkaibusError


class BizkaibusParseError(BizkaibusError):
    """Raised when the service response is malformed or unexpected."""
