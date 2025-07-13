
from bizkaibus.ServiceParams import BizkaibusServiceParam

class LineItinerary(BizkaibusServiceParam):

    def GetParams(self) -> dict:
        """Retrieve the parameters for the service."""
        params = {}
        params['callback'] = ''
        params['strLinea'] = ''
        params['strParada'] = ''
        return params
    
    def GetParams(self, line: str) -> dict:
        """Retrieve the parameters for the service."""
        params = {}
        params['callback'] = ''
        params['sCodigoLinea'] = line
        params['sNumeroRuta'] = line
        params['sSentido'] = 'I'
        return params
        