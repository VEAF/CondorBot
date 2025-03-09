import yaml
import logging
import os
from pydantic import BaseModel
from functools import cache
from rich import print

logger = logging.getLogger("config")


class DiscordConfig(BaseModel):
    api_token: str
    admin_channel_id: int


class CondorServerConfig(BaseModel):
    server_name: str = "Default Server Name"
    port: int = 56278
    password: str | None = None
    max_players: int = 32
    max_spectators: int = 32
    max_ping: int = 500
    join_time_limit: int = 10
    max_two_planes: int = 8
    advertise_on_web: bool = False
    automatic_port_forwarding: bool = True
    advertise_manual_ip: str | None = None
    allow_clients_to_save_flight_plan: bool = True


class Config(BaseModel):
    discord: DiscordConfig

    condor_server: CondorServerConfig
    flight_plans_path: str
    condor_path: str


def load_config(filename: str) -> Config:
    logger.debug(f"loading config file {filename}")

    if not os.path.isfile(filename):
        raise FileNotFoundError(f"configuration file {filename} not found")

    with open(filename, "r") as file:
        raw_config = yaml.safe_load(file)

        return Config.model_validate(raw_config)


@cache
def get_config() -> Config:
    return load_config(filename="config.yaml")


def check_config(config: Config):
    errors: int = 0
    if not os.path.isdir(config.flight_plans_path):
        errors += 1
        print("flight_plans_path [blue]{config.flight_plans_path}[/blue] [red]NOT EXISTS[/red]")

    if errors:
        raise Exception("configuration has errors, see logs for more information")

    print("config is [green]OK[/green]")
