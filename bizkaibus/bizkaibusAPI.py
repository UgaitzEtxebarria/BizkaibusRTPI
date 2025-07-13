"""Support for Bizkaibus, Biscay (Basque Country, Spain) Bus service."""

import xml.etree.ElementTree as ET
import json
import aiohttp

from Model.BizkaibusArrival import BizkaibusArrival
from Model.BizkaibusArrivalTime import BizkaibusArrivalTime
from Model.BizkaibusLine import BizkaibusLine
from Model.BizkaibusTimetable import BizkaibusTimetable
from .const import _RESOURCE
from typing import Optional

class BizkaibusAPI:
    """The class for handling the data retrieval."""

    def __init__(self, stop: str):
        """Initialize the data object."""
        self.stop = stop
        
    async def TestConnection(self) -> bool: 
        """Test the API."""
        result = await self.__connect(self.stop)
        return result is not None
    
    async def GetLinesOnStop(self, stopId) -> list[str]:
        """Retrieve the information of a bus on stop."""
        result = await self.__connect(self.stop)
        if result is None:
            return []

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

        return []

    async def GetTimetable(self) -> Optional[BizkaibusTimetable]:
        """Retrieve the information of a stop arrivals."""
        return await self.__getTimetable()

    async def GetNextArrivals(self, line) -> Optional[BizkaibusArrival]:
        """Retrieve the information of a bus on stop."""
        timetable = await self.__getTimetable()

        if timetable is None or not timetable.arrivals or line not in timetable.arrivals:
            return None
        else:
            return timetable.arrivals[line]
            
    async def __connect(self, stop) -> Optional[dict[str, str]]:
        async with aiohttp.ClientSession() as session:
            params = self.__getTimetableParams(stop)
            async with session.get(_RESOURCE, params=params) as response:
                if response.status != 200:
                    return None

                strJSON = await response.text()
                strJSON = strJSON[1:-2].replace('\'', '"')
                result = json.loads(strJSON)

                if str(result['STATUS']) != 'OK':
                    return None
                
                return result

    async def __getTimetable(self) -> Optional[BizkaibusTimetable]:
        result = await self.__connect(self.stop)
        if result is None:
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

        return timetable
    
    def __getLinesOnTownParams(self, stop):
        params = {}
        params['callback'] = ''
        params['strLinea'] = ''
        params['strParada'] = stop
        return params
    
    def __getLinesOnStopParams(self, stop):
        params = {}
        params['callback'] = ''
        params['strLinea'] = ''
        params['strParada'] = stop
        return params