from .bizkaibus_error import BizkaibusError


class BizkaibusConnectionError(BizkaibusError):
    """Raised when a request to the Bizkaibus service cannot be completed."""