from enum import IntEnum
import psutil
from pydantic import BaseModel, Field
from rich import print
from condor.flight_plan import BOT_FLIGHT_PLAN_LIST, get_default_flight_plans_list_path, save_flight_plans_list
from condor.config import get_config
import os
from pywinauto import Application
from pywinauto.application import WindowSpecification

CONDOR_DEDICATED_EXE = "CondorDedicated.exe"

condor_app: Application | None = None
condor_window: WindowSpecification | None = None


class OnlineStatus(IntEnum):
    OFFLINE = 0  # CondorDediacted.exe is not launched
    RUNNING = 1  # CondorDediacted.exe is running
    JOINING_ENABLED = 2  # Game is launched, server is listening on TCP/UDP, players can join
    RACE_IN_PROGRESS = 3  # Game is launched, server is listening on TCP/UDP, only spectators can join
    JOINING_DISABLED = 4  # unknown state when race is finished @toco


class ServerStatus(BaseModel):
    online_status: OnlineStatus = OnlineStatus.OFFLINE
    time: str | None = None
    stop_join_in: str | None = None
    players: list[str] = Field(default_factory=list)


class CondorProcess(BaseModel):
    name: str
    cmdline: list[str]
    pid: int


def is_server_running() -> CondorProcess | None:
    for process in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
        if process.info["name"] == CONDOR_DEDICATED_EXE:
            return CondorProcess.model_validate(process.info)
    return None


def save_host_ini() -> None:
    config = get_config()
    host_ini: dict[str, str] = {}

    host_ini["ServerName"] = config.condor_server.server_name
    host_ini["Port"] = config.condor_server.port
    host_ini["Password"] = config.condor_server.password
    host_ini["AdminPassword"] = config.condor_server.admin_password
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
    global condor_app, condor_window

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


def parse_server_status_list_box_items(status: ServerStatus, list_box_items) -> None:
    raw_status = {}
    for item in list_box_items:
        key, value = str(item).split(":", 1)
        raw_status[key] = value.strip()

    if "Status" not in raw_status:
        status.online_status = OnlineStatus.RUNNING
    elif raw_status["Status"] == "joining enabled":
        status.online_status = OnlineStatus.JOINING_ENABLED
    elif raw_status["Status"] == "race in progress":
        status.online_status = OnlineStatus.RACE_IN_PROGRESS
    else:
        status.online_status = OnlineStatus.JOINING_DISABLED

    status.time = raw_status.get("Time", None)
    status.stop_join_in = raw_status.get("Stop join in", None)


def parse_players_list_box_items(status: ServerStatus, list_box_items) -> None:
    players = []
    for item in list_box_items:
        players.append(item)

    status.players = players


def refresh_server_status() -> ServerStatus:
    # @todo refresh server status, check labels, check buttons, etc...

    if not condor_app or not condor_window:
        if not attach_server():
            return ServerStatus(online_status=OnlineStatus.OFFLINE)

    # a better way than searching all listbox, and matching the top position ?
    list_boxes = condor_window.descendants(class_name="TspListBox")
    server_status_list_box = None
    players_list_box = None

    # SERVER_NAME_LIST_ID = 0
    SERVER_STATUS_LIST_ID = 1
    # SERVER_FPL_LIST_ID = 2
    SERVER_PLAYERS_LIST_ID = 3
    for list_box_id, list_box in enumerate(list_boxes):
        if list_box_id == SERVER_STATUS_LIST_ID:
            server_status_list_box = list_box
        if list_box_id == SERVER_PLAYERS_LIST_ID:
            players_list_box = list_box

    if not server_status_list_box:
        raise Exception("server status list not found in condor server window")

    status = ServerStatus()
    parse_server_status_list_box_items(status, server_status_list_box.item_texts())
    parse_players_list_box_items(status, players_list_box.item_texts())

    return status


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
    refresh_server_status()
