from ..const import _RESOURCE, TIMETABLE_SERVICE
from .bizkaibus_service_param import BizkaibusServiceParam


class TimetableServiceParam(BizkaibusServiceParam):

    def __init__(self, stop: str):
        """Retrieve the parameters for the service."""
        super().__init__()
        self.params["strLinea"] = ""
        self.params["strParada"] = stop

    def get_url(self) -> str:
        return _RESOURCE + TIMETABLE_SERVICE
