from bizkaibus import BizkaibusAPI, BizkaibusLanguages
from bizkaibus.Model.BizkaibusArrival import BizkaibusArrival
from bizkaibus.Model.BizkaibusArrivalTime import BizkaibusArrivalTime
from bizkaibus.Model.BizkaibusLine import BizkaibusLine
from bizkaibus.Model.BizkaibusTimetable import BizkaibusTimetable
from bizkaibus.ServiceParams.BizkaibusServiceParam import ResponseType
from bizkaibus.ServiceParams.TimetableServiceParam import TimetableServiceParam
from bizkaibus.const import _RESOURCE, TIMETABLE_SERVICE


def test_timetable_service_param_exposes_compatible_api():
    service = TimetableServiceParam("0296")

    assert service.response_type == ResponseType.JSON
    assert service.get_url() == _RESOURCE + TIMETABLE_SERVICE
    assert service.build_params()["strParada"] == "0296"
    assert service.build_params()["callback"] == ""



def test_package_exports_public_api():
    assert BizkaibusAPI is not None
    assert BizkaibusLanguages is not None


def test_arrival_uses_pythonic_attribute_names():
    arrival = BizkaibusArrival(
        BizkaibusLine("A", "Ruta 1"),
        nearest_arrival=BizkaibusArrivalTime(3),
        next_arrival=BizkaibusArrivalTime(8),
    )

    assert arrival.nearest_arrival.time == 3


def test_line_and_timetable_use_pythonic_attributes():
    line = BizkaibusLine(line_id="A", route="Ruta 1")
    assert line.line_id == "A"
    assert line.id == "A"
    assert line.route_name == "Ruta 1"

    timetable = BizkaibusTimetable(stop_id="0296", stop_name="Parada Central")
    assert timetable.stop_id == "0296"
    assert timetable.id == "0296"
    assert timetable.stop_name == "Parada Central"
    assert timetable.name == "Parada Central"


def test_arrival_time_exposes_pythonic_minutes_alias():
    time_value = BizkaibusArrivalTime(12)
    assert time_value.minutes == 12
    assert time_value.time == 12
