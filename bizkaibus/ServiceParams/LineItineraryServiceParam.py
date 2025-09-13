from ServiceParams.BizkaibusServiceParam import BizkaibusServiceParam
from const import _RESOURCE, LINES_ITINERARY_SERVICE

class LineItineraryServiceParam(BizkaibusServiceParam):

    def __init__(self, line_Id: str, stop: str, direction: str):
        """Retrieve the parameters for the service."""
        
        self.params['sCodigoLinea'] = line_Id
        self.params['sNumeroRuta'] = stop
        self.params['sSentido'] = direction

    def GetURL(self) -> str:
        return _RESOURCE + LINES_ITINERARY_SERVICE