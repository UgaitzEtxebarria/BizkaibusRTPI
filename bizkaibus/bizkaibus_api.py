"""Support for Bizkaibus, Biscay (Basque Country, Spain) Bus service."""

from __future__ import annotations

import asyncio
import json
import xml.etree.ElementTree as ET
from typing import Any, Optional
from xml.etree.ElementTree import Element

import aiohttp

from .Exceptions import (
    BizkaibusConnectionError,
    BizkaibusParseError,
    BizkaibusStopNotFoundError,
)
from .Model.bizkaibus_arrival import BizkaibusArrival
from .Model.bizkaibus_arrival_time import BizkaibusArrivalTime
from .Model.bizkaibus_languages import BizkaibusLanguages
from .Model.bizkaibus_line import BizkaibusLine
from .Model.bizkaibus_timetable import BizkaibusTimetable
from .ServiceParams.bizkaibus_service_param import BizkaibusServiceParam, ResponseType
from .ServiceParams.line_itinerary_service_param import LineItineraryServiceParam
from .ServiceParams.lines_in_town_service_param import LinesInTownServiceParam
from .ServiceParams.stop_info_service_param import StopInfoServiceParam
from .ServiceParams.timetable_service_param import TimetableServiceParam


class BizkaibusAPI:
    """The class for handling the data retrieval."""

    _MAX_CONCURRENT_ITINERARY_REQUESTS = 5

    def __init__(self, language: BizkaibusLanguages, stop: str):
        """Initialize the data object."""
        self.stop = stop
        self.language = language
        self._session: Optional[aiohttp.ClientSession] = None
        self._owns_session = True
        self._location: tuple[str, str] | None = None

    @classmethod
    async def create(
        cls,
        language: BizkaibusLanguages,
        stop: str,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> "BizkaibusAPI":
        api = cls(language, stop)
        if session is not None:
            api._session = session
            api._owns_session = False

        try:
            await api.__get_location()
        except BaseException:
            await api.close()
            raise

        return api

    async def __aenter__(self) -> "BizkaibusAPI":
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the HTTP session used by this client."""
        session = self._session
        self._session = None
        if self._owns_session and session is not None and not session.closed:
            await session.close()

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

        try:
            line_records = result["Consulta"]["Lineas"]
            if not isinstance(line_records, list):
                raise BizkaibusParseError("Unexpected line list in Bizkaibus response")
        except (KeyError, TypeError) as exc:
            raise BizkaibusParseError("Invalid lines response from Bizkaibus") from exc

        unique_lines = {}

        for line in line_records:
            try:
                route = line["NumeroRuta"]
                line_id = line["CodigoLinea"]
                direction = line["Sentido"]
            except (KeyError, TypeError) as exc:
                raise BizkaibusParseError("Invalid line record in Bizkaibus response") from exc

            unique_lines.setdefault(line_id, []).append((line, route, direction))

        unique_lines = dict(
            sorted(unique_lines.items(), key=lambda item: len(item[1]), reverse=True)
        )
        semaphore = asyncio.Semaphore(self._MAX_CONCURRENT_ITINERARY_REQUESTS)

        async def get_line_for_stop(line_id, line_variants):
            for line_info, route, direction in line_variants:
                itinerary = LineItineraryServiceParam(line_id, route, direction)
                async with semaphore:
                    itinerary_response = await self.__get_response(itinerary)
                if itinerary_response is None:
                    continue
                try:
                    itinerary_stops = itinerary_response["Consulta"]
                    stop_records = itinerary_stops["Paradas"]
                    route_name = itinerary_stops["Descripcion"]
                    if not isinstance(stop_records, list):
                        raise BizkaibusParseError("Unexpected stop list in itinerary response")
                except (KeyError, TypeError) as exc:
                    raise BizkaibusParseError("Invalid itinerary response from Bizkaibus") from exc

                try:
                    for stop in stop_records:
                        if stop["PR_CODRED"] == self.stop:
                            incident = self.__get_incident_string(line_info, self.language)
                            return BizkaibusLine(line_id, route_name, incident)
                except (KeyError, TypeError) as exc:
                    raise BizkaibusParseError("Invalid stop record in itinerary response") from exc

            return None

        line_ids = list(unique_lines)
        results = await asyncio.gather(
            *(get_line_for_stop(line_id, unique_lines[line_id]) for line_id in line_ids),
            return_exceptions=True,
        )

        lines = []
        for result in results:
            if isinstance(result, BaseException):
                raise result
            if result is not None:
                lines.append(result)

        return lines

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
        if self._location is not None:
            return self._location

        stop_info_param = StopInfoServiceParam()
        stop_response = await self.__get_response(stop_info_param)

        internal_xml = stop_response.text or ""

        internal_xml = internal_xml.removeprefix("1®").strip()

        try:
            consulta = ET.fromstring(internal_xml)
        except ET.ParseError as exc:
            raise BizkaibusParseError("Invalid XML in stop information response") from exc

        records = consulta.findall("Registro")
        if not records:
            raise BizkaibusParseError("Stop information response contains no stop records")

        stop = next(
            (registro for registro in records if registro.get("CODIGOREDUCIDOPARADA") == self.stop),
            None,
        )

        if stop is None:
            raise BizkaibusStopNotFoundError(self.stop)

        province = stop.get("PROVINCIA", "")
        municipality = stop.get("MUNICIPIO", "")

        self._location = (province, municipality)
        return self._location

    def __get_incident_string(self, lineInfo, currentLanguage: BizkaibusLanguages) -> str | None:
        if currentLanguage == BizkaibusLanguages.EU:
            return lineInfo["IncidenciaEuskera"]
        elif currentLanguage == BizkaibusLanguages.ES:
            return lineInfo["IncidenciaCastellano"]
        else:
            return None

    async def __get_timetable(self) -> Optional[BizkaibusTimetable]:
        timetable_param = TimetableServiceParam(self.stop)
        result = await self.__get_response(timetable_param)
        if result is None:
            return None

        try:
            root = ET.fromstring(result["Resultado"])
        except (ET.ParseError, KeyError, TypeError) as exc:
            raise BizkaibusParseError("Invalid timetable response from Bizkaibus") from exc

        stop_name = root.find("DenominacionParada")
        stop_name_str = stop_name.text if stop_name is not None else None
        timetable = BizkaibusTimetable(self.stop, stop_name_str)

        for childBus in root.findall("PasoParada"):
            linea_elem = childBus.find("linea")
            ruta_elem = childBus.find("ruta")
            e1_elem = childBus.find("e1")
            e2_elem = childBus.find("e2")

            route = linea_elem.text if linea_elem is not None else None
            route_name = ruta_elem.text if ruta_elem is not None else None
            minutes1 = e1_elem.find("minutos") if e1_elem is not None else None
            time1 = minutes1.text if minutes1 is not None else None
            minutes2 = e2_elem.find("minutos") if e2_elem is not None else None
            time2 = minutes2.text if minutes2 is not None else None

            if route_name is not None and time1 is not None and route is not None:
                try:
                    if time2 is None:
                        stop_arrival = BizkaibusArrival(
                            BizkaibusLine(route, route_name), BizkaibusArrivalTime(int(time1))
                        )
                    else:
                        stop_arrival = BizkaibusArrival(
                            BizkaibusLine(route, route_name),
                            BizkaibusArrivalTime(int(time1)),
                            BizkaibusArrivalTime(int(time2)),
                        )
                except ValueError as exc:
                    raise BizkaibusParseError("Invalid arrival time in timetable response") from exc

                timetable.arrivals[stop_arrival.line.id] = stop_arrival

        return timetable

    async def __get_response(self, service_param: BizkaibusServiceParam) -> Any:
        if service_param.response_type == ResponseType.JSON:
            return await self.__get_json(service_param)
        return await self.__get_xml(service_param)

    async def __get_json(self, service_param: BizkaibusServiceParam) -> Optional[dict[str, Any]]:
        string = await self.__get_raw_request(service_param)

        try:
            str_JSON = string[1:-2].replace("'", '"')
            result = json.loads(str_JSON)
            if not isinstance(result, dict) or "STATUS" not in result:
                raise BizkaibusParseError("Unexpected JSON response from Bizkaibus")
        except (json.JSONDecodeError, TypeError) as exc:
            raise BizkaibusParseError("Invalid JSON response from Bizkaibus") from exc

        if str(result["STATUS"]) != "OK":
            raise BizkaibusConnectionError(
                f"Bizkaibus service returned status {result['STATUS']!r}"
            )

        return result

    async def __get_xml(self, service_param: BizkaibusServiceParam) -> Optional[Element]:
        response = await self.__get_raw_request(service_param)

        try:
            return ET.fromstring(response)
        except ET.ParseError as exc:
            raise BizkaibusParseError("Invalid XML response from Bizkaibus") from exc

    async def __get_raw_request(self, service_param: BizkaibusServiceParam) -> str:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=20)
            self._session = aiohttp.ClientSession(timeout=timeout)
            self._owns_session = True

        params = service_param.build_params()
        url = service_param.get_url()
        try:
            async with self._session.get(url, params=params) as response:
                if response.status != 200:
                    raise BizkaibusConnectionError(
                        f"Bizkaibus request to {url} failed with HTTP status {response.status}"
                    )

                return await response.text()
        except asyncio.TimeoutError as exc:
            raise BizkaibusConnectionError(f"Bizkaibus request to {url} timed out") from exc
        except aiohttp.ClientError as exc:
            raise BizkaibusConnectionError(
                f"Could not complete Bizkaibus request to {url}: {exc}"
            ) from exc
