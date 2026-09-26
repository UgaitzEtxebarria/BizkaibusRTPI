from .BizkaibusError import BizkaibusError


class BizkaibusStopNotFoundError(BizkaibusError):
    """Raised when the requested stop does not exist in the service."""

    def __init__(self, stop_id: str):
        self.stop_id = stop_id
        super().__init__(f"The stop id '{stop_id}' does not exist")