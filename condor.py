from math import sqrt
from pydantic import BaseModel
from discord import Client
import configparser
import psutil
from rich import print
from config import Config, get_config
import os
from pywinauto import Application
from pywinauto.application import WindowSpecification

BOT_FLIGHT_PLAN_LIST = "condor_bot.sfl"
CONDOR_DEDICATED_EXE = "CondorDedicated.exe"

condor_app: Application | None = None
condor_window: WindowSpecification | None = None
condor_test = None


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


class CondorProcess(BaseModel):
    name: str
    cmdline: list[str]
    pid: int


def load_flight_plan(filename: str) -> FlightPlan:
    parser = configparser.ConfigParser()
    parser.read(filename, encoding="utf-8")

    flightplan = {}
    flightplan["filename"] = filename.split("/")[-1]
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


def is_server_running() -> CondorProcess | None:
    for process in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
        if process.info["name"] == CONDOR_DEDICATED_EXE:
            return CondorProcess.model_validate(process.info)
    return None


def get_default_flight_plans_list_path() -> str:
    return f"{get_config().condor_path}\\{BOT_FLIGHT_PLAN_LIST}"


def save_flight_plans_list(flight_plans: list[str]) -> None:
    with open(get_default_flight_plans_list_path(), "wt") as file:
        for flight_plan in flight_plans:
            print(f"writing {flight_plan} to list")
            file.write(f"{get_config().flight_plans_path}\\{flight_plan}\n")


def save_host_ini() -> None:
    config = get_config()
    host_ini: dict[str, str] = {}

    host_ini["ServerName"] = config.condor_server.server_name
    host_ini["Port"] = config.condor_server.port
    host_ini["Password"] = config.condor_server.password
    host_ini["MaxPlayers"] = config.condor_server.max_players
    host_ini["MaxSpectators"] = config.condor_server.max_spectators
    host_ini["MaxPing"] = config.condor_server.max_ping
    host_ini["JoinTimeLimit"] = config.condor_server.join_time_limit
    host_ini["MaxTowplanes"] = config.condor_server.max_two_planes
    host_ini["AdvertiseOnWeb"] = int(config.condor_server.advertise_on_web)
    host_ini["AutomaticPortForwarding"] = int(config.condor_server.automatic_port_forwarding)
    host_ini["AdvertiseManualIP"] = config.condor_server.advertise_manual_ip
    host_ini["AllowClientsToSaveFlightPlan"] = int(config.condor_server.allow_clients_to_save_flight_plan)

    host_ini_path = f"{config.condor_path}/Settings/Host.ini"
    with open(host_ini_path, "wt") as file:
        lines: list[str] = []
        lines.append("[General]")

        for key, value in host_ini.items():
            lines.append(f"{key}={value if value else ''}")
        lines.append("[DedicatedServer]")
        lines.append(f"LastSFL={get_default_flight_plans_list_path()}")

        file.writelines([line + "\n" for line in lines])


def get_flight_plan_path(flight_plan_filename: str) -> str:
    return f"{get_config().flight_plans_path}/{flight_plan_filename}"


def start_server(flight_plan_filename: str) -> bool:
    config = get_config()

    if process := is_server_running():
        raise Exception(f"condor server is already running, pid={process.pid}")

    flight_plan_filepath = get_flight_plan_path(flight_plan_filename)

    if not os.path.isfile(flight_plan_filepath):
        raise Exception(f"flight plan {flight_plan_filename} not found")

    save_host_ini()
    print("[blue]Host.ini[/blue] [yellow]saved[/yellow]")
    save_flight_plans_list(flight_plans=[flight_plan_filename])
    print(f"flight plans list [blue]{BOT_FLIGHT_PLAN_LIST}[/blue] [yellow]saved[/yellow]")

    try:
        old_path = os.getcwd()
        os.chdir(config.condor_path)
        condor_app = Application().start(cmd_line=f"{config.condor_path}\\{CONDOR_DEDICATED_EXE}")
        os.chdir(old_path)
    except Exception:
        os.chdir(old_path)
        return False

    condor_window = condor_app.window(title_re="Condor dedicated server.*", class_name="TDedicatedForm")
    condor_window.child_window(title="START", class_name="TspSkinButton").click()

    return True


def refresh_server_status() -> None:
    # @todo refresh server status, check labels, check buttons, etc...
    pass


def attach_server() -> bool:
    if not is_server_running():
        print("[red]condor server is not running[/red] couldn't attach")
        return False

    global condor_app, condor_window

    condor_app = Application().connect(path=CONDOR_DEDICATED_EXE)
    condor_window = condor_app.window(title_re="Condor dedicated server.*", class_name="TDedicatedForm")

    if not condor_window:
        print("[red]condor server main window not found[/red]")
        return False
    print("[yellow]condor server main window attached[/yellow]")

    return True


def stop_server() -> None:
    global condor_app, condor_window

    if not condor_app or not condor_window:
        raise Exception("condor app or window are not attached")
    
    if condor_window.child_window(title="STOP", class_name="TspSkinButton").exists():
        condor_window.child_window(title="STOP", class_name="TspSkinButton").click()

        confirm_window = condor_app.window(title="Confirm")
        confirm_window.child_window(title="OK", class_name="TspSkinButton").click()

        condor_window.child_window(title="START", class_name="TspSkinButton").wait(wait_for="visible")

    condor_app.kill()

    condor_app = None
    condor_window = None

    return True


if __name__ == "__main__":
    # just for basic tests...
    fp = load_flight_plan("tests/test.fpl")
    print(fp.landscape)
    print(f"distance: {fp.distance}")

    for tp in fp.turnpoints:
        print(tp)

    process = is_server_running()
    print("Condor Server:", end=" ")
    if isinstance(process, CondorProcess):
        print(f"[green]running[/green] (pid {process.pid} - {process.cmdline})")
    else:
        print("[red]not running[/red]")
        start_server(flight_plan_filename="Ajdovscina_100_km_ridge.fpl")
