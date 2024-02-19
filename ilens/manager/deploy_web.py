from io import StringIO
import os
from pyinfra.operations import apt, files, server, git, pip, systemd
from pyinfra.api import deploy
from pyinfra.facts.server import Which
from pyinfra import host


PROJECT_REPO = "https://github.com/Ilens-NextGen/ilens-api.git"
PROJECT_SRC = "/home/ubuntu/projects/ilens-api"
PROJECT_BRANCH = "main"
SERVICE_FILE = "/etc/systemd/system/ilens.service"
LOGGLY_TOKEN = ""


def ensure_local():
    """Ensure that the user is able to run pyinfra locally."""
    dotenv_paths = [".env", ".env.prod", ".prod.env"]
    ssh_config_path = os.path.expanduser("~/.ssh/config")

    # env file must exist
    if not any(map(os.path.exists, dotenv_paths)):
        raise RuntimeError("No env file found")
    # ssh config must exist
    if not os.path.exists(ssh_config_path):
        raise RuntimeError("No ssh config found")
    # ssh key must exist
    if not os.path.exists(os.path.expanduser("~/.ssh/nextgen")):
        raise RuntimeError("No ssh key found")


def _getenvvars() -> dict[str, str]:
    """set environment variables for the host"""
    envvars: dict[str, str] = {}
    if host.data.get("name"):
        envvars["SERVER_ID"] = host.data.name
    if host.data.get("port"):
        envvars["PORT"] = str(host.data.port)
    return envvars


@deploy("Setup Server")
def setup_server():
    sudo = bool(host.get_fact(Which, "sudo"))
    has_pip = bool(host.get_fact(Which, "pip3"))
    has_python = bool(host.get_fact(Which, "python3.10"))

    if has_python:
        return
    apt.update(
        name="Update apt cache",
        cache_time=3600,
        _sudo=sudo,
    )
    apt.packages(
        name="Install common packages",
        packages=["software-properties-common", "curl", "git"],
        _sudo=sudo,
    )
    apt.ppa(
        name="Add deadsnakes PPA",
        src="ppa:deadsnakes/ppa",
        _sudo=sudo,
    )
    apt.packages(
        name="Install python3.10",
        packages=["python3.10", "python3.10-distutils"],
        _sudo=sudo,
    )
    if has_pip:
        return
    files.download(
        name="Download get-pip.py",
        src="https://bootstrap.pypa.io/get-pip.py",
        dest="get-pip.py",
        _sudo=sudo,
    )
    server.shell(
        name="Install pip3.10",
        commands=[
            "python3.10 get-pip.py",
        ],
        _sudo=sudo,
    )
    files.link(
        name="Link pip3.10 to pip3",
        path="/usr/bin/pip3",
        target="/usr/local/bin/pip3.10",
        force=True,
        _sudo=sudo,
    )


@deploy("Setup Loggly")
def setup_loggly():
    # is sudo available?
    sudo = bool(host.get_fact(Which, "sudo"))
    apt.packages(
        name="Install rsyslog",
        packages=["rsyslog"],
        _sudo=sudo,
    )
    files.template(
        name="Create rsyslog config",
        src="ilens/manager/templates/22-loggly.conf.j2",
        dest="/etc/rsyslog.d/22-loggly.conf",
        _sudo=sudo,
        loggly_token=LOGGLY_TOKEN,
        loggly_tag="ilens",
        server_id=host.data.name,
    )
    files.line(
        name="Set max message size",
        path="/etc/rsyslog.conf",
        line="$MaxMessageSize .*",
        replace="$MaxMessageSize 64k",
        _sudo=sudo,
    )
    files.line(
        name="Enable UDP",
        path="/etc/rsyslog.conf",
        line=r"#\s*\$ModLoad imudp",
        replace="$ModLoad imudp",
        _sudo=sudo,
    )
    files.line(
        name="Enable UDP",
        path="/etc/rsyslog.conf",
        line=r"#\s*\$UDPServerRun 514",
        replace="$UDPServerRun 514",
        _sudo=sudo,
    )
    systemd.service(
        name="Restart rsyslog",
        service="rsyslog",
        running=True,
        restarted=True,
        daemon_reload=True,
        _sudo=sudo,
    )


@deploy("Install Project")
def install_project():
    sudo = bool(host.get_fact(Which, "sudo"))
    for env_file in [".env.prod", ".prod.env", ".env"]:
        if not os.path.exists(env_file):
            continue
        with open(env_file) as f:
            env_vars = StringIO(f.read())
        break
    else:
        raise FileNotFoundError("No env file found")
    files.directory(
        name="Create project directory",
        path=PROJECT_SRC,
        present=True,
    )
    git.repo(
        name="Fetch source code",
        src=PROJECT_REPO,
        dest=PROJECT_SRC,
        branch=PROJECT_BRANCH,
        pull=True,
    )
    pip.packages(
        name="Install requirements",
        requirements=f"{PROJECT_SRC}/requirements.txt",
        pip="pip3",
    )
    apt.packages(
        name="Install ffmpeg",
        packages=["ffmpeg"],
        _sudo=sudo,
    )
    files.template(
        name="Create .env file",
        src=env_vars,
        dest=f"{PROJECT_SRC}/.env",
        **_getenvvars(),
    )
    files.template(
        name="Create systemd service",
        src="ilens/manager/templates/ilens.service.j2",
        dest=SERVICE_FILE,
        project_src=PROJECT_SRC,
        _sudo=sudo,
    )
    systemd.service(
        name="Start iLens service",
        service="ilens",
        running=True,
        restarted=True,
        daemon_reload=True,
        _env=_getenvvars(),
        _sudo=sudo,
    )


@deploy("Deploy App")
def deploy_web():
    ensure_local()
    setup_server()
    # disabled loggly for now
    # setup_loggly()
    install_project()


deploy_web()
