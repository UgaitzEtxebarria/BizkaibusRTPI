import asyncio
from typing import cast

import aiohttp
import pytest

from bizkaibus import (
    BizkaibusAPI,
    BizkaibusConnectionError,
    BizkaibusError,
    BizkaibusLanguages,
    BizkaibusParseError,
    BizkaibusStopNotFoundError,
)
from bizkaibus.const import (
    _RESOURCE,
    LINES_ITINERARY_SERVICE,
    LINES_PER_TOWN_SERVICE,
    STOP_INFO_SERVICE,
    TIMETABLE_SERVICE,
)
from bizkaibus.Exceptions import BizkaibusConnectionError as ExceptionConnectionError
from bizkaibus.Exceptions import BizkaibusParseError as ExceptionParseError
from bizkaibus.Exceptions import BizkaibusStopNotFoundError as ExceptionStopNotFoundError
from bizkaibus.Model.bizkaibus_arrival import BizkaibusArrival
from bizkaibus.Model.bizkaibus_arrival_time import BizkaibusArrivalTime
from bizkaibus.Model.bizkaibus_line import BizkaibusLine
from bizkaibus.Model.bizkaibus_timetable import BizkaibusTimetable
from bizkaibus.ServiceParams.bizkaibus_service_param import ResponseType
from bizkaibus.ServiceParams.line_itinerary_service_param import LineItineraryServiceParam
from bizkaibus.ServiceParams.lines_in_town_service_param import LinesInTownServiceParam
from bizkaibus.ServiceParams.stop_info_service_param import StopInfoServiceParam
from bizkaibus.ServiceParams.timetable_service_param import TimetableServiceParam


def test_package_exports_public_api():
    assert BizkaibusAPI is not None
    assert BizkaibusLanguages is not None
    assert BizkaibusError is not None
    assert BizkaibusConnectionError is not None
    assert BizkaibusParseError is not None
    assert BizkaibusStopNotFoundError is not None


def test_response_type_and_languages_are_enums():
    assert ResponseType.JSON.value == "json"
    assert ResponseType.XML.value == "xml"
    assert BizkaibusLanguages.ES.value == "es"
    assert BizkaibusLanguages.EU.value == "eu"


def test_service_param_urls_and_params_are_correct():
    timetable = TimetableServiceParam("0296")
    assert timetable.get_url() == _RESOURCE + TIMETABLE_SERVICE
    assert timetable.build_params()["strParada"] == "0296"
    assert timetable.response_type == ResponseType.JSON

    stop_info = StopInfoServiceParam()
    assert stop_info.get_url() == _RESOURCE + STOP_INFO_SERVICE
    assert stop_info.response_type == ResponseType.XML

    lines_in_town = LinesInTownServiceParam("48", "Bilbao")
    assert lines_in_town.get_url() == _RESOURCE + LINES_PER_TOWN_SERVICE
    assert lines_in_town.build_params()["iCodigoProvincia"] == "48"
    assert lines_in_town.build_params()["sCodigoMunicipio"] == "Bilbao"

    itinerary = LineItineraryServiceParam("A", "Ruta 1", "1")
    assert itinerary.get_url() == _RESOURCE + LINES_ITINERARY_SERVICE
    assert itinerary.line_id == "A"
    itinerary.line_id = "B"
    assert itinerary.line_id == "B"


def test_line_and_arrival_models_are_pythonic_and_safe():
    line = BizkaibusLine("A", "Ruta 1")
    assert line.id == "A"
    assert line.route == "Ruta 1"
    assert line.incident is None
    assert str(line) == "(A) Ruta 1"

    line_with_incident = BizkaibusLine("A", "Ruta 1", "Incidencia")
    assert line_with_incident.incident == "Incidencia"
    assert str(line_with_incident) == "*(A) Ruta 1"

    arrival_time = BizkaibusArrivalTime(12)
    assert arrival_time.time == 12
    assert isinstance(arrival_time.get_utc(), str)
    assert isinstance(arrival_time.get_absolute(), str)

    arrival = BizkaibusArrival(
        line,
        nearest_arrival=arrival_time,
        next_arrival=BizkaibusArrivalTime(20),
    )
    assert arrival.nearest_arrival.time == 12
    assert arrival.next_arrival.time == 20
    assert "Ruta 1" in str(arrival)

    timetable = BizkaibusTimetable("0296", "Parada Central")
    assert timetable.id == "0296"
    assert timetable.name == "Parada Central"
    assert timetable.arrivals == {}

    timetable.arrivals["A"] = arrival
    assert timetable.arrivals["A"].line.id == "A"
    assert "Parada Central" in str(timetable)


def test_timetable_instances_do_not_share_state():
    first = BizkaibusTimetable("1", "A")
    second = BizkaibusTimetable("2", "B")

    first.arrivals["A"] = BizkaibusArrival(BizkaibusLine("A", "Ruta 1"), BizkaibusArrivalTime(5))

    assert "A" not in second.arrivals
    assert second.arrivals == {}


def test_exceptions_are_exported_and_message_is_descriptive():
    assert issubclass(BizkaibusConnectionError, BizkaibusError)
    assert issubclass(BizkaibusParseError, BizkaibusError)
    assert issubclass(BizkaibusStopNotFoundError, BizkaibusError)

    err = BizkaibusStopNotFoundError("9999")
    assert err.stop_id == "9999"
    assert "9999" in str(err)

    assert ExceptionConnectionError.__name__ == "BizkaibusConnectionError"
    assert ExceptionParseError.__name__ == "BizkaibusParseError"
    assert ExceptionStopNotFoundError.__name__ == "BizkaibusStopNotFoundError"


@pytest.mark.asyncio
async def test_create_and_context_manager_manage_session(monkeypatch):
    api = BizkaibusAPI(BizkaibusLanguages.EU, "0296")

    async def fake_location():
        return ("48", "Bilbao")

    monkeypatch.setattr(api, "_BizkaibusAPI__get_location", fake_location)

    created = await BizkaibusAPI.create(BizkaibusLanguages.EU, "0296")
    assert isinstance(created, BizkaibusAPI)
    assert created.stop == "0296"

    class AsyncSession:
        closed = False

        async def close(self):
            self.closed = True

    created._session = cast(aiohttp.ClientSession, AsyncSession())
    await created.__aexit__(None, None, None)
    assert created._session is not None

    async with BizkaibusAPI(BizkaibusLanguages.EU, "0296") as api_ctx:
        assert api_ctx.language == BizkaibusLanguages.EU


@pytest.mark.asyncio
async def test_get_lines_on_stop_parses_valid_response(monkeypatch):
    api = BizkaibusAPI(BizkaibusLanguages.EU, "0296")

    async def fake_location():
        return ("48", "Bilbao")

    async def fake_response(service_param):
        if service_param.__class__.__name__ == "LinesInTownServiceParam":
            return {
                "Consulta": {
                    "Lineas": [
                        {
                            "NumeroRuta": "Ruta 1",
                            "CodigoLinea": "A",
                            "Sentido": "1",
                            "IncidenciaEuskera": "Varios",
                        }
                    ]
                }
            }
        if service_param.__class__.__name__ == "LineItineraryServiceParam":
            return {
                "Consulta": {
                    "Paradas": [{"PR_CODRED": "0296"}],
                    "Descripcion": "Ruta 1",
                }
            }
        return None

    monkeypatch.setattr(api, "_BizkaibusAPI__get_location", fake_location)
    monkeypatch.setattr(api, "_BizkaibusAPI__get_response", fake_response)

    lines = await api.get_lines_on_stop()
    assert len(lines) == 1
    assert lines[0].id == "A"
    assert lines[0].incident == "Varios"


@pytest.mark.asyncio
async def test_get_timetable_parses_xml_response(monkeypatch):
    api = BizkaibusAPI(BizkaibusLanguages.ES, "0296")

    xml_response = """
    <Resultado>
        <DenominacionParada>Parada Central</DenominacionParada>
        <PasoParada>
            <linea>A</linea>
            <ruta>Ruta 1</ruta>
            <e1><minutos>5</minutos></e1>
            <e2><minutos>12</minutos></e2>
        </PasoParada>
    </Resultado>
    """

    async def fake_response(_service_param):
        return {"Resultado": xml_response}

    monkeypatch.setattr(api, "_BizkaibusAPI__get_response", fake_response)

    timetable = await api.get_timetable()
    assert timetable is not None
    assert timetable.name == "Parada Central"
    assert "A" in timetable.arrivals
    assert timetable.arrivals["A"].nearest_arrival.time == 5
    assert timetable.arrivals["A"].next_arrival.time == 12


@pytest.mark.asyncio
async def test_get_next_arrivals_returns_none_for_missing_lines(monkeypatch):
    api = BizkaibusAPI(BizkaibusLanguages.EU, "0296")

    async def fake_timetable():
        return BizkaibusTimetable("0296", "Parada Central")

    monkeypatch.setattr(api, "_BizkaibusAPI__get_timetable", fake_timetable)

    assert await api.get_next_arrivals("Z") is None


@pytest.mark.asyncio
async def test_raw_request_raises_connection_error_on_timeout_and_http_errors():
    class TimedOutRequest:
        async def __aenter__(self):
            raise asyncio.TimeoutError

        async def __aexit__(self, exc_type, exc_value, traceback):
            return False

    class Session:
        closed = False

        def __init__(self):
            self.calls = 0

        def get(self, url, params):
            self.calls += 1
            return TimedOutRequest()

    api = BizkaibusAPI(BizkaibusLanguages.EU, "0296")
    api._session = cast(aiohttp.ClientSession, Session())

    with pytest.raises(BizkaibusConnectionError, match="timed out"):
        await api._BizkaibusAPI__get_raw_request(TimetableServiceParam("0296"))

    class BadResponse:
        status = 500
        url = "https://example.test"

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_value, traceback):
            return False

    class SessionWithStatus:
        closed = False

        def get(self, url, params):
            return BadResponse()

    api._session = cast(aiohttp.ClientSession, SessionWithStatus())
    with pytest.raises(BizkaibusConnectionError, match="HTTP status"):
        await api._BizkaibusAPI__get_raw_request(TimetableServiceParam("0296"))


@pytest.mark.asyncio
async def test_parse_errors_for_invalid_json_and_xml(monkeypatch):
    api = BizkaibusAPI(BizkaibusLanguages.EU, "0296")

    async def fake_raw(_service_param):
        return "xnot-jsonxx"

    monkeypatch.setattr(api, "_BizkaibusAPI__get_raw_request", fake_raw)
    with pytest.raises(BizkaibusParseError, match="Invalid JSON"):
        await api._BizkaibusAPI__get_json(TimetableServiceParam("0296"))

    async def fake_raw_xml(_service_param):
        return "<response>"

    monkeypatch.setattr(api, "_BizkaibusAPI__get_raw_request", fake_raw_xml)
    with pytest.raises(BizkaibusParseError, match="Invalid XML"):
        await api._BizkaibusAPI__get_xml(StopInfoServiceParam())


@pytest.mark.asyncio
async def test_stop_not_found_raises_when_location_missing(monkeypatch):
    api = BizkaibusAPI(BizkaibusLanguages.EU, "9999")

    async def fake_response(_service_param):
        return type(
            "Response",
            (),
            {"text": "<Paradas><Registro CODIGOREDUCIDOPARADA='1111' PROVINCIA='48' MUNICIPIO='Bilbao'/></Paradas>"},
        )()

    monkeypatch.setattr(api, "_BizkaibusAPI__get_response", fake_response)
    with pytest.raises(BizkaibusStopNotFoundError):
        await api._BizkaibusAPI__get_location()
