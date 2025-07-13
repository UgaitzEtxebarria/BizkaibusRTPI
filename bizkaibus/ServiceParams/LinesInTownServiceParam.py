
class LinesInTownServiceParam(BizkaibusServiceParam):

    def GetParams(self, stop: str) -> dict:
        """Retrieve the parameters for the service."""
        params = {}
        params['callback'] = ''
        params['iCodigoProvincia'] = ''
        params['sCodigoMunicipio'] = stop
        params['sDescripcionMunicipio'] = stop
        return params
        