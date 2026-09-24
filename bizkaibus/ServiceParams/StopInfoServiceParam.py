from .BizkaibusServiceParam import BizkaibusServiceParam, ResponseType
from ..const import _RESOURCE, STOP_INFO_SERVICE

class StopInfoServiceParam(BizkaibusServiceParam):
    response_type = ResponseType.XML

    def __init__(self):
        """Retrieve the parameters for the service."""
        super().__init__()


    def get_url(self) -> str:
        return _RESOURCE + STOP_INFO_SERVICE