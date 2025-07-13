
class TimetableServiceParam(BizkaibusServiceParam):

    def GetParams(self, stop: str) -> dict:
        """Retrieve the parameters for the service."""
        params = {}
        params['callback'] = ''
        params['strLinea'] = ''
        params['strParada'] = stop
        return params
        