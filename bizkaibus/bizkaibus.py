"""Support for Bizkaibus, Biscay (Basque Country, Spain) Bus service."""

import xml.etree.ElementTree as ET

import json
import aiohttp
import datetime

_RESOURCE = 'http://apli.bizkaia.net/'
_RESOURCE += 'APPS/DANOK/TQWS/TQ.ASMX/GetPasoParadaMobile_JSON'

ATTR_ROUTE = 'Route'
ATTR_ROUTE_NAME = 'Route name'
ATTR_DUE_IN = 'Due in'

CONF_STOP_ID = 'stopid'
CONF_ROUTE = 'route'

DEFAULT_NAME = 'Next bus'

class BizkaibusLine:
    id: str = ''
    route: str = ''

    def __init__(self, id, route):
        """Initialize the data object."""
        self.id = id
        self.route = route

    def __str__(self):
        """Return a string representation of the object."""
        return f"({self.id}) {self.route}"


class BizkaibusArrivalTime:
    time: int = 0

    def __init__(self, time: int):
        """Initialize the data object."""
        self.time = time

    def GetUTC(self):
        """Get the time in UTC format."""
        now = datetime.datetime.now(datetime.timezone.utc)
        time = (now + datetime.timedelta(minutes=int(self.time))).isoformat()
        return time

    def GetAbsolute(self):
        """Get the time in absolute format."""
        now = datetime.datetime.now()
        time = (now + datetime.timedelta(minutes=int(self.time))).isoformat()
        return time

    def __str__(self):
        """Return a string representation of the object."""
        return f"{self.time} min"


from typing import Optional

class BizkaibusArrival:
    line: BizkaibusLine
    closestArrival: BizkaibusArrivalTime
    farestArrival: Optional[BizkaibusArrivalTime] = None

    def __init__(self, line: BizkaibusLine, closestArrival: BizkaibusArrivalTime, farestArrival: Optional[BizkaibusArrivalTime] = None):
        """Initialize the data object."""
        self.line = line
        self.closestArrival = closestArrival
        self.farestArrival = farestArrival
    
    def __str__(self):
        """Return a string representation of the object."""
        return f"Line: {self.line}, closest: {self.closestArrival}, farest: {self.farestArrival}"

class BizkaibusTimetable:
    """The class for handling the data retrieval."""
    id: str = ''
    name: str | None = ''
    arrivals: dict[str, BizkaibusArrival] = {}

    def __init__(self, id: str, name: str | None):
        """Initialize the data object."""
        self.id = id
        self.name = name

    def __str__(self):
        """Return a string representation of the object."""

        arrivals_str = ', '.join(str(arrival) for arrival in self.arrivals.values())
        return f"Stop: ({self.id}) {self.name}, arrivals: {arrivals_str}"

class BizkaibusData:
    """The class for handling the data retrieval."""

    def __init__(self, stop: str):
        """Initialize the data object."""
        self.stop = stop
        self.__setUndefined()
        
    async def TestConnection(self):
        """Test the API."""
        result = await self.__connect(self.stop)
        return result != None

    async def GetTimetable(self) -> Optional[BizkaibusTimetable]:
        """Retrieve the information of a stop arrivals."""
        return await self.__getTimetable()

    async def GetNextBus(self, line) -> Optional[BizkaibusArrival]:
        """Retrieve the information of a bus on stop."""
        timetable = await self.__getTimetable()

        if timetable is None or not timetable.arrivals or line not in timetable.arrivals:
            return None
        else:
            return timetable.arrivals[line]
            
    async def __connect(self, stop) -> Optional[dict[str, str]]:
        async with aiohttp.ClientSession() as session:
            params = self.__getAPIParams(stop)
            async with session.get(_RESOURCE, params=params) as response:
                if response.status != 200:
                    self.__setUndefined()
                    return None

                strJSON = await response.text()
                strJSON = strJSON[1:-2].replace('\'', '"')
                result = json.loads(strJSON)

                if str(result['STATUS']) != 'OK':
                    self.__setUndefined()
                    return None
                
                return result

    async def __getTimetable(self) -> Optional[BizkaibusTimetable]:
        result = await self.__connect(self.stop)
        if result is None:
            self.__setUndefined()
            return None

        root = ET.fromstring(result['Resultado'])

        stopName = root.find('DenominacionParada')
        stopNameStr = stopName.text if stopName is not None else None
        timetable = BizkaibusTimetable(self.stop, stopNameStr)

        for childBus in root.findall("PasoParada"):
            linea_elem = childBus.find('linea')
            ruta_elem = childBus.find('ruta')
            e1_elem = childBus.find('e1')
            e2_elem = childBus.find('e2')

            route = linea_elem.text if linea_elem is not None else None
            routeName = ruta_elem.text if ruta_elem is not None else None
            minutos1 = e1_elem.find('minutos') if e1_elem is not None else None
            time1 = minutos1.text if minutos1 is not None else None
            minutos2 = e2_elem.find('minutos') if e2_elem is not None else None
            time2 = minutos2.text if minutos2 is not None else None

            if (routeName is not None and time1 is not None and route is not None):
                if time2 is None:
                     stopArrival = BizkaibusArrival(BizkaibusLine(route, routeName), 
                    BizkaibusArrivalTime(int(time1)))
                else:
                    stopArrival = BizkaibusArrival(BizkaibusLine(route, routeName), 
                    BizkaibusArrivalTime(int(time1)), BizkaibusArrivalTime(int(time2)))

                timetable.arrivals[stopArrival.line.id] = stopArrival

        if not timetable.arrivals:
            self.__setUndefined()

        return timetable

    def __getAPIParams(self, stop):
        params = {}
        params['callback'] = ''
        params['strLinea'] = ''
        params['strParada'] = stop

        return params

    def __setUndefined(self):
        self.info = [{ATTR_ROUTE_NAME: 'n/a',
                          ATTR_DUE_IN: 'n/a'}]