"""Support for Bizkaibus, Biscay (Basque Country, Spain) Bus service."""

import xml.etree.ElementTree as ET

import json
import aiohttp
from xml.etree.ElementTree import Element

from .Exceptions.StopNotFoundError import StopNotFoundError
from .Model.BizkaibusArrival import BizkaibusArrival
from .Model.BizkaibusArrivalTime import BizkaibusArrivalTime
from .Model.BizkaibusLanguages import BizkaibusLanguages
from .Model.BizkaibusLine import BizkaibusLine
from .Model.BizkaibusTimetable import BizkaibusTimetable
from .ServiceParams.BizkaibusServiceParam import BizkaibusServiceParam, ResponseType
from .ServiceParams.LineItineraryServiceParam import LineItineraryServiceParam
from .ServiceParams.LinesInTownServiceParam import LinesInTownServiceParam
from .ServiceParams.TimetableServiceParam import TimetableServiceParam
from .ServiceParams.StopInfoServiceParam import StopInfoServiceParam
from typing import Any, Optional


class BizkaibusAPI:
    """The class for handling the data retrieval."""

    def __init__(self, language: BizkaibusLanguages, stop: str):
        """Initialize the data object."""
        self.stop = stop
        self.language = language
        self._session: Optional[aiohttp.ClientSession] = None

    @classmethod
    async def create(
        cls,
        language: BizkaibusLanguages,
        stop: str
    ) -> "BizkaibusAPI":
        api = cls(language, stop)

        try:
            if not await api.__get_location():
                raise ValueError(f"Cannot connect")
        except Exception:
            await api.close()
            raise

        return api

    async def __aenter__(self) -> "BizkaibusAPI":
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the HTTP session used by this client."""
        if self._session is not None and not self._session.closed:
            await self._session.close()
        
    async def test_connection(self) -> bool: 
        """Test the API."""
        timetable_param = TimetableServiceParam(self.stop)
        result = await self.__get_response(timetable_param)
        return result is not None
    
    async def get_lines_on_stop(self) -> list[BizkaibusLine]:
        """Retrieve the information of a bus on stop."""

        location = await self.__get_location()
        if location is None:
            return []

        province, municipality = location

        timetable_param = LinesInTownServiceParam(province, municipality)
        result = await self.__get_response(timetable_param)
        if result is None:
            return []

        root = result['Consulta']
 
        lines = {}

        for line in root['Lineas']:
            route = line['NumeroRuta']
            line_id = line['CodigoLinea']
            direction = line['Sentido']

            if line_id in lines:
                continue

            itinerary = LineItineraryServiceParam(line_id, route, direction)

            itinerary_response = await self.__get_response(itinerary)
            if itinerary_response is None:
                continue
            itinerary_stops = itinerary_response['Consulta']

            for stop in itinerary_stops['Paradas']:
                if stop['PR_CODRED'] == self.stop:
                    incident = self.__get_incident_string(line, self.language)
                    lines[line_id] = BizkaibusLine(line_id, itinerary_stops['Descripcion'], incident)
                    break

        return list(lines.values())

    async def get_timetable(self) -> Optional[BizkaibusTimetable]:
        """Retrieve the information of a stop arrivals."""
        return await self.__get_timetable()

    async def get_next_arrivals(self, line: str) -> Optional[BizkaibusArrival]:
        """Retrieve the information of a bus on stop."""
        timetable = await self.__get_timetable()

        if timetable is None or not timetable.arrivals or line not in timetable.arrivals:
            return None
        else:
            return timetable.arrivals[line]

    async def __get_location(self) -> tuple[str, str] | None:

        stop_info_param = StopInfoServiceParam()
        stop_response = await self.__get_response(stop_info_param)
        
        if stop_response is None:
            return None

        internal_xml = stop_response.text or ""

        internal_xml = internal_xml.removeprefix("1®").strip()

        consulta = ET.fromstring(internal_xml)

        stop = next(
            (
                registro
                for registro in consulta.findall('Registro')
                if registro.get('CODIGOREDUCIDOPARADA') == self.stop
            ),
            None,
        )

        if stop is None:
            raise StopNotFoundError(self.stop)

        province = stop.get('PROVINCIA', '')
        municipality = stop.get('MUNICIPIO', '')

        return province, municipality

        
    def __get_incident_string(self, lineInfo, currentLanguage: BizkaibusLanguages) -> str | None:
        if currentLanguage == BizkaibusLanguages.EU:
            return lineInfo['IncidenciaEuskera']
        elif currentLanguage == BizkaibusLanguages.ES:
            return lineInfo['IncidenciaCastellano']
        else:
            return None

    

    async def __get_timetable(self) -> Optional[BizkaibusTimetable]:
        timetable_param = TimetableServiceParam(self.stop)
        result = await self.__get_response(timetable_param)
        if result is None:
            return None

        root = ET.fromstring(result['Resultado'])

        stop_name = root.find('DenominacionParada')
        stop_name_str = stop_name.text if stop_name is not None else None
        timetable = BizkaibusTimetable(self.stop, stop_name_str)

        for childBus in root.findall("PasoParada"):
            linea_elem = childBus.find('linea')
            ruta_elem = childBus.find('ruta')
            e1_elem = childBus.find('e1')
            e2_elem = childBus.find('e2')

            route = linea_elem.text if linea_elem is not None else None
            route_name = ruta_elem.text if ruta_elem is not None else None
            minutes1 = e1_elem.find('minutos') if e1_elem is not None else None
            time1 = minutes1.text if minutes1 is not None else None
            minutes2 = e2_elem.find('minutos') if e2_elem is not None else None
            time2 = minutes2.text if minutes2 is not None else None

            if (route_name is not None and time1 is not None and route is not None):
                if time2 is None:
                    stop_arrival = BizkaibusArrival(BizkaibusLine(route, route_name), 
                    BizkaibusArrivalTime(int(time1)))
                else:
                    stop_arrival = BizkaibusArrival(BizkaibusLine(route, route_name), 
                    BizkaibusArrivalTime(int(time1)), BizkaibusArrivalTime(int(time2)))

                timetable.arrivals[stop_arrival.line.id] = stop_arrival

        return timetable

    async def __get_response(self, service_param: BizkaibusServiceParam) -> Any:
        if service_param.response_type == ResponseType.JSON:
            return await self.__get_json(service_param)
        return await self.__get_xml(service_param)

    async def __get_json(self, service_param: BizkaibusServiceParam) -> Optional[dict[str, Any]]:
        string = await self.__get_raw_request(service_param)
        
        str_JSON = string[1:-2].replace('\'', '"')
        result = json.loads(str_JSON)

        if str(result['STATUS']) != 'OK':
            return None
        
        return result
    
    async def __get_xml(self, service_param: BizkaibusServiceParam) -> Optional[Element]:
        response = await self.__get_raw_request(service_param)

        return ET.fromstring(response)

    async def __get_raw_request(self, service_param: BizkaibusServiceParam) -> str:
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=20)
            self._session = aiohttp.ClientSession(timeout=timeout)

        params = service_param.build_params()
        url = service_param.get_url()
        async with self._session.get(url, params=params) as response:
            if response.status != 200:
                raise ConnectionError(f"Bizkaibus request failed with status {response.status} for {url}")

            return await response.text()
