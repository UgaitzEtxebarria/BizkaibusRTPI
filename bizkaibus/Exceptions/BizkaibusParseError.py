from .BizkaibusError import BizkaibusError


class BizkaibusParseError(BizkaibusError):
    """Raised when the service response is malformed or unexpected."""