from math import sqrt
from pydantic import BaseModel
from discord import Client
import configparser
import psutil
from rich import print
from config import Config, get_config
import os
from pywinauto import Application

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


def check_server_is_running() -> CondorProcess | None:
    for process in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
        if process.info["name"] == "CondorDedicated.exe":
            return CondorProcess.model_validate(process.info)
    return None


def get_default_flight_plans_list_path(config: Config) -> str:
    return f"{config.condor_path}\\{BOT_FLIGHT_PLAN_LIST}"


def save_flight_plans_list(flight_plans: list[str], config: Config) -> None:
    with open(get_default_flight_plans_list_path(config=config), "wt") as file:
        for flight_plan in flight_plans:
            print(f"writing {flight_plan} to list")
            file.write(f"{config.flight_plans_path}\\{flight_plan}\n")


def save_host_ini(config: Config) -> None:
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
        lines.append(f"LastSFL={get_default_flight_plans_list_path(config=config)}")

        file.writelines([line + "\n" for line in lines])


def start_server(config: Config, flight_plan_filename: str, client: Client | None = None) -> bool:
    if process := check_server_is_running():
        print(f"[red]condor server is already running[/red], pid={process.pid}")
        return False

    flight_plan_filepath = f"{config.flight_plans_path}/{flight_plan_filename}"

    if not os.path.isfile(flight_plan_filepath):
        print(
            f"[red]flight plan [blue]{flight_plan_filename}[/red] not found in [yellow]{config.flight_plans_path}[/yellow]"
        )
        return False

    save_host_ini(config=config)
    print("[blue]Host.ini[/blue] [yellow]saved[/yellow]")
    save_flight_plans_list(flight_plans=[flight_plan_filename], config=config)
    print(f"flight plans list [blue]{BOT_FLIGHT_PLAN_LIST}[/blue] [yellow]saved[/yellow]")

    # shutil.copy(flight_plan_filepath, f"{config.user_documents_path}/Flightplan.fpl")
    # print("[blue]Flightplan.fpl[/blue] [yellow]saved[/yellow]")

    # subprocess.Popen([config.condor_server_exe])

    try:
        old_path = os.getcwd()
        os.chdir(config.condor_path)
        condor_app = Application().start(cmd_line=f"{config.condor_path}\\CondorDedicated.exe")
        os.chdir(old_path)
    except Exception:
        os.chdir(old_path)

    # for window in app.windows():
    #     print(f"Titre: {window.window_text()}, Classe: {window.class_name()}")

    window = condor_app.window(title_re="Condor dedicated server.*", class_name="TDedicatedForm")

    # window.dump_tree()
    # for item in window.():
    #     print(f"Titre: {window.window_text()}, Classe: {window.class_name()}")

    window.child_window(title="START", class_name="TspSkinButton").click()
    # sleep(5)

    # print("[blue]CondorServer[/blue] [yellow]started[/yellow]")


def stop_server() -> None:
    # @todo
    pass


# au démarrage du serveur:

# fichiers modifiés dans C:\Users\mitch\OneDrive\Documents\Condor3\Pilots\NAME_Firstname
# C:\Users\veaf\Documents\Condor3\Pilots\NAME_Firstname

# Host.ini
# [General]
# ServerName=Default Server Name
# Port=56278
# Password=
# MaxPlayers=32
# MaxSpectators=32
# MaxPing=60
# JoinTimeLimit=10
# MaxTowplanes=8
# AdvertiseOnWeb=0
# AutomaticPortForwarding=1
# AdvertiseManualIP=
# AllowClientsToSaveFlightPlan=1

# Flightplan.fpl mis à jour


if __name__ == "__main__":
    fp = load_flight_plan("tests/test.fpl")
    print(fp.landscape)
    print(f"distance: {fp.distance}")

    for tp in fp.turnpoints:
        print(tp)

    process = check_server_is_running()
    print("Condor Server:", end=" ")
    if isinstance(process, CondorProcess):
        print(f"[green]running[/green] (pid {process.pid} - {process.cmdline})")
    else:
        print("[red]not running[/red]")
        start_server(config=get_config(), flight_plan_filename="Ajdovscina_100_km_ridge.fpl")
