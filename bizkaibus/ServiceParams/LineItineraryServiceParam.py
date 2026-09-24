from .BizkaibusServiceParam import BizkaibusServiceParam
from ..const import _RESOURCE, LINES_ITINERARY_SERVICE

class LineItineraryServiceParam(BizkaibusServiceParam):

    def __init__(self, line_id: str, stop: str, direction: str):
        """Retrieve the parameters for the service."""
        super().__init__()
        self.params['sCodigoLinea'] = line_id
        self.params['sNumeroRuta'] = stop
        self.params['sSentido'] = direction

    @property
    def line_id(self) -> str:
        return self.params['sCodigoLinea']

    @line_id.setter
    def line_id(self, value: str) -> None:
        self.params['sCodigoLinea'] = value

    def get_url(self) -> str:
        return _RESOURCE + LINES_ITINERARY_SERVICE