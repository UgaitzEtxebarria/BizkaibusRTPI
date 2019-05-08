"""Support for Bizkaibus, Biscay (Basque Country, Spain) Bus service."""

import xml.etree.ElementTree as ET

import json
import requests
import datetime

_RESOURCE = 'http://apli.bizkaia.net/'
_RESOURCE += 'APPS/DANOK/TQWS/TQ.ASMX/GetPasoParadaMobile_JSON'

ATTR_ROUTE = 'Route'
ATTR_ROUTE_NAME = 'Route name'
ATTR_DUE_IN = 'Due in'

CONF_STOP_ID = 'stopid'
CONF_ROUTE = 'route'

DEFAULT_NAME = 'Next bus'

class BizkaibusData:
    """The class for handling the data retrieval."""

    def __init__(self, stop, route):
        """Initialize the data object."""
        self.stop = stop
        self.route = route
        self.info = [{ATTR_ROUTE_NAME: 'n/a',
                      ATTR_ROUTE: self.route,
                      ATTR_DUE_IN: 'n/a'}]

    def getNextBus(self, isRelative, isUTC):
        """Retrieve the information from API."""
        params = {}
        params['callback'] = ''
        params['strLinea'] = self.route
        params['strParada'] = self.stop

        response = requests.get(_RESOURCE, params, timeout=10)

        if response.status_code != 200:

            self.info = [{ATTR_ROUTE_NAME: 'n/a',
                          ATTR_ROUTE: self.route,
                          ATTR_DUE_IN: 'n/a'}]
            return

        strJSON = response.text[1:-2].replace('\'', '"')
        result = json.loads(strJSON)

        if str(result['STATUS']) != 'OK':
            self.info = [{ATTR_ROUTE_NAME: 'n/a',
                          ATTR_ROUTE: self.route,
                          ATTR_DUE_IN: 'n/a'}]
            return

        root = ET.fromstring(result['Resultado'])

        self.info = []
        for childBus in root.findall("PasoParada"):
            route = childBus.find('linea').text
            routeName = childBus.find('ruta').text
            time = childBus.find('e1').find('minutos').text

            if (routeName is not None and time is not None and
                    route is not None and route == self.route):
                if not isRelative:
                    if isUTC:
                        now = datetime.datetime.utcnow()
                    else:
                        now = datetime.datetime.now()
                    time = (now + datetime.timedelta(minutes=int(time))).isoformat()
                bus_data = {ATTR_ROUTE_NAME: routeName,
                            ATTR_ROUTE: route,
                            ATTR_DUE_IN: time}
                self.info.append(bus_data)

        if not self.info:
            self.info = [{ATTR_ROUTE_NAME: 'n/a',
                          ATTR_ROUTE: self.route,
                          ATTR_DUE_IN: 'n/a'}]

