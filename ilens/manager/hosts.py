import json
from pathlib import Path
from typing import TypedDict
from ilens.server.utils import getenv, loadenv
import requests
from os.path import expanduser, exists

loadenv()

BIN_URL = getenv("JSONBIN_URL")
BIN_HEADERS = {
    "X-Access-Key": getenv("JSONBIN_ACCESS_KEY"),
    "Content-Type": "application/json",
}
SSH_CONFIG_FILE = expanduser(getenv("SSH_CONFIG_FILE"))
SSH_IDENTITY_FILE = expanduser(getenv("SSH_IDENTITY_FILE"))
SERVER_LOCAL_BIN = Path(__file__).parent / "servers.json"

assert exists(SSH_IDENTITY_FILE), f"{SSH_IDENTITY_FILE} does not exist"


class Server(TypedDict):
    name: str
    host: str
    port: int
    user: str


def fetch_servers() -> dict[str, list[Server]]:
    response = requests.get(BIN_URL, headers=BIN_HEADERS)
    response.raise_for_status()
    servers: dict[str, list[Server]] = response.json()["record"]
    return servers


def load_servers() -> dict[str, tuple[str, dict]]:
    with open(SERVER_LOCAL_BIN, "r") as file:
        servers: dict[str, list[Server]] = json.load(file)
    return {
        group: list(
            (
                server["name"],
                {
                    "name": server["name"],
                    "host": server["host"],
                    "port": server["port"],
                },
            )
            for server in servers
        )
        for group, servers in servers.items()
    }


def update_ssh_config(servers: dict[str, list[Server]]):
    with open(SSH_CONFIG_FILE, "w") as file:
        for _, group_servers in servers.items():
            for server in group_servers:
                file.write(f"Host {server['name']}\n")
                file.write(f"  HostName {server['host']}\n")
                file.write(f"  User {server['user']}\n")
                file.write(f"  IdentityFile {SSH_IDENTITY_FILE}\n")
                file.write("\n")


if not SERVER_LOCAL_BIN.exists():
    raise RuntimeError(
        "inventory does not exist!\n" "Run `ilens fetch-inventory` to download it."
    )
servers = load_servers()
loadbalancer = servers.pop("loadbalancer")
backend = servers.pop("backend")
