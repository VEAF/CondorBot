import pytest
from unittest.mock import patch
from condor.flight_plan import (
    TurnPoint,
    FlightPlan,
    flight_plan_to_markdown,
    list_flight_plans,
    load_flight_plan,
    get_flight_plan_path,
    save_flight_plans_list,
)


def test_turnpoint_creation():
    tp = TurnPoint(name="Start", pos_x=0.0, pos_y=0.0, pos_z=1000.0, airport_id=1, radius=500, altitude=1200)
    assert tp.name == "Start"
    assert tp.pos_x == 0.0
    assert tp.pos_y == 0.0
    assert tp.pos_z == 1000.0
    assert tp.airport_id == 1
    assert tp.radius == 500
    assert tp.altitude == 1200


def test_flightplan_distance():
    turnpoints = [
        TurnPoint(name="Start", pos_x=0.0, pos_y=0.0, pos_z=1000.0, airport_id=1, radius=500, altitude=1200),
        TurnPoint(name="Middle", pos_x=3.0, pos_y=4.0, pos_z=1000.0, airport_id=2, radius=500, altitude=1300),
        TurnPoint(name="End", pos_x=6.0, pos_y=8.0, pos_z=1000.0, airport_id=3, radius=500, altitude=1400),
    ]
    fp = FlightPlan(
        filepath="test.sfl",
        version="1.0",
        landscape="TestLand",
        description="A test flight plan",
        turnpoints=turnpoints,
    )
    assert 10.0 == pytest.approx(fp.distance, 0.01)


def test_load_flight_plan():
    fp = load_flight_plan("tests/files/test.fpl")
    assert isinstance(fp, FlightPlan)
    assert fp.filename == "test.fpl"
    assert fp.version == "3000"
    assert fp.landscape == "Slovenia3"
    assert fp.description == "100 km of evening ridge riding"
    assert len(fp.turnpoints) == 6
    assert pytest.approx(fp.distance, 0.01) == 107855

    tp = fp.turnpoints[0]
    assert isinstance(tp, TurnPoint)
    assert tp.name == "Ajdovscina"
    assert pytest.approx(tp.pos_x, 0.001) == 231523.859375
    assert pytest.approx(tp.pos_y, 0.001) == 59637.1015625
    assert pytest.approx(tp.pos_z, 0.001) == 114.0
    assert tp.airport_id == 1
    assert tp.radius == 3000
    assert tp.altitude == 1500


def test_list_flight_plans(mock_config):
    fpl = list_flight_plans()

    assert len(fpl) == 2

    fp = fpl[0]
    assert isinstance(fp, FlightPlan)
    assert fp.filepath == "tests\\files\\test.fpl"
    assert fp.filename == "test.fpl"
    assert fp.human_filename == "test"
    assert fp.landscape == "Slovenia3"


def test_flight_plan_to_markdown() -> None:
    flight_plan = FlightPlan(filepath="test.fpl", version="30000", landscape="AA3", description="Mon plan de vol")
    for i in range(3):
        flight_plan.turnpoints.append(
            TurnPoint(name=f"TP{i:01}", pos_x=i * 10000, pos_y=i * 1000, pos_z=0, airport_id=0, radius=1, altitude=1000)
        )
    # Act
    markdown = flight_plan_to_markdown(flight_plan)
    print(markdown)

    # Assert
    wanted_markdown = """**Flight Plan**: test.fpl
**Length**: 20 km
**Turn points**: 3
- TP0
- TP1
- TP2
"""
    assert markdown == wanted_markdown
