from math import sqrt
from pydantic import BaseModel
import configparser
from rich import print
from condor.config import get_config

BOT_FLIGHT_PLAN_LIST = "condor_bot.sfl"


class TurnPoint(BaseModel):
    name: str
    pos_x: float
    pos_y: float
    pos_z: float
    airport_id: int
    radius: int
    altitude: int


class PlaneClass(BaseModel):
    name: str


class FlightPlan(BaseModel):
    filename: str
    version: str
    landscape: str
    description: str
    turnpoints: list[TurnPoint]

    @property
    def distance(self) -> float:
        total_dist = 0

        for i in range(1, len(self.turnpoints) - 1):
            point_from = self.turnpoints[i - 1]
            point_to = self.turnpoints[i]
            total_dist += sqrt((point_to.pos_x - point_from.pos_x) ** 2 + (point_to.pos_y - point_from.pos_y) ** 2)

        return total_dist


def load_flight_plan(filepath: str) -> FlightPlan:
    parser = configparser.ConfigParser()
    parser.read(filepath, encoding="utf-8")

    print(filepath)

    flightplan = {}
    flightplan["filename"] = filepath.split("/")[-1]
    flightplan["version"] = parser.get("Version", "Condor version", fallback=None)
    flightplan["landscape"] = parser.get("Task", "Landscape", fallback=None)
    flightplan["description"] = parser.get("Description", "Text", fallback=None)
    flightplan["turnpoints"] = []

    flightplan["plane_class"] = {
        "class": parser.get("Plane", "Class", fallback=None),
        "name": parser.get("Plane", "Name", fallback=None),
        "water": int(parser.get("Plane", "Water", fallback=0)),
    }

    nb_turnpoints = parser.getint("Task", "Count", fallback=0)
    for i in range(nb_turnpoints):
        tp = {
            "name": parser.get("Task", f"TPName{i}", fallback=None),
            "pos_x": float(parser.get("Task", f"TPPosX{i}", fallback=0)),
            "pos_y": float(parser.get("Task", f"TPPosY{i}", fallback=0)),
            "pos_z": float(parser.get("Task", f"TPPosZ{i}", fallback=0)),
            "airport_id": int(parser.get("Task", f"TPAirport{i}", fallback=0)),
            "radius": int(parser.get("Task", f"TPRadius{i}", fallback=0)),
            "altitude": int(parser.get("Task", f"TPAltitude{i}", fallback=0)),
        }
        flightplan["turnpoints"].append(tp)

    return FlightPlan.model_validate(flightplan)


def get_default_flight_plans_list_path() -> str:
    return f"{get_config().condor_path}\\{BOT_FLIGHT_PLAN_LIST}"


def save_flight_plans_list(flight_plans: list[str]) -> None:
    with open(get_default_flight_plans_list_path(), "wt") as file:
        for flight_plan in flight_plans:
            print(f"writing {flight_plan} to list")
            file.write(f"{get_config().flight_plans_path}\\{flight_plan}\n")


def get_flight_plan_path(flight_plan_filename: str) -> str:
    """Get the absolute flight plan path for specified flight plan filename"""
    return f"{get_config().flight_plans_path}/{flight_plan_filename}"
