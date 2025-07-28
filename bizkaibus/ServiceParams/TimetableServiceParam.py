from bizkaibus.ServiceParams.BizkaibusServiceParam import BizkaibusServiceParam
from bizkaibus.const import _RESOURCE, TIMETABLE_SERVICE

class TimetableServiceParam(BizkaibusServiceParam):

    def __init__(self, stop: str):
        """Retrieve the parameters for the service."""
        
        self.params['strLinea'] = ''
        self.params['strParada'] = stop

    def GetURL(self) -> str:
        return _RESOURCE + TIMETABLE_SERVICE