from .BizkaibusServiceParam import BizkaibusServiceParam
from const import _RESOURCE, LINES_PER_TOWN_SERVICE

class LinesInTownServiceParam(BizkaibusServiceParam):

    def __init__(self, province: str, stop: str):
        """Retrieve the parameters for the service."""
        
        self.params['iCodigoProvincia'] = province
        self.params['sCodigoMunicipio'] = stop
        self.params['sDescripcionMunicipio'] = ""

    def GetURL(self) -> str:
        return _RESOURCE + LINES_PER_TOWN_SERVICE
