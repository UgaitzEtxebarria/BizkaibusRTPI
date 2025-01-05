"""Support for Bizkaibus, Biscay (Basque Country, Spain) Bus service."""

import asyncio
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
        time = (now + datetime.timedelta(minutes=int(time))).isoformat()
        return time

    def GetAbsolute(self):
        """Get the time in absolute format."""
        now = datetime.datetime.now()
        time = (now + datetime.timedelta(minutes=int(time))).isoformat()
        return time

    def __str__(self):
        """Return a string representation of the object."""
        return f"{self.time} min"


class BizkaibusArrival:
    line: BizkaibusLine = None
    closestArrival: BizkaibusArrivalTime = None
    farestArrival: BizkaibusArrivalTime = None

    def __init__(self, line: BizkaibusLine, closestArrival: BizkaibusArrivalTime, farestArrival: BizkaibusArrivalTime):
        """Initialize the data object."""
        self.line = line
        self.closestArrival = closestArrival
        self.farestArrival = farestArrival
    
    def __str__(self):
        """Return a string representation of the object."""
        return f"Line: {self.line}, closest: {self.closestArrival}, farest: {self.farestArrival}"

class BizkaibusTimetable:
    """The class for handling the data retrieval."""
    stop: str = ''
    arrivals: dict[str, BizkaibusArrival] = {}

    def __init__(self, stop: str):
        """Initialize the data object."""
        self.stop = stop

    def __str__(self):
        """Return a string representation of the object."""

        arrivals_str = ', '.join(str(arrival) for arrival in self.arrivals.values())
        return f"Stop: {self.stop}, arrivals: {arrivals_str}"

class BizkaibusData:
    """The class for handling the data retrieval."""

    def __init__(self, stop: str):
        """Initialize the data object."""
        self.stop = stop
        self.__setUndefined()
        
    async def TestConnection(self):
        """Test the API."""
        result = await self.__connect(self.stop)
        return result != False

    async def GetTimetable(self) -> BizkaibusTimetable:
        """Retrieve the information of a stop arrivals."""
        return await self.__getTimetable()

    async def GetNextBus(self, line) -> BizkaibusArrival:
        """Retrieve the information of a bus on stop."""
        timetable = await self.__getTimetable()
        return timetable.arrivals[line]
            
    async def __connect(self, stop):
        async with aiohttp.ClientSession() as session:
            params = self.__getAPIParams(stop)
            async with session.get(_RESOURCE, params=params) as response:
                if response.status != 200:
                    self.__setUndefined()
                    return False

                strJSON = await response.text()
                strJSON = strJSON[1:-2].replace('\'', '"')
                result = json.loads(strJSON)

                if str(result['STATUS']) != 'OK':
                    self.__setUndefined()
                    return False
                
                return result

    async def __getTimetable(self) -> BizkaibusTimetable:
        result = await self.__connect(self.stop)
        if result == False:
            self.__setUndefined()
            return False

        root = ET.fromstring(result['Resultado'])

        timetable = BizkaibusTimetable(self.stop)

        for childBus in root.findall("PasoParada"):
            route = childBus.find('linea').text
            routeName = childBus.find('ruta').text
            time1 = childBus.find('e1').find('minutos').text
            time2 = childBus.find('e2').find('minutos').text

            if (routeName is not None and time1 is not None and route is not None):
                stopArrival = BizkaibusArrival(BizkaibusLine(route, routeName), 
                    BizkaibusArrivalTime(time1), BizkaibusArrivalTime(time2))
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



