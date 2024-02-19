from pyinfra import host
from pyinfra.operations import apt, server, files, systemd
from pyinfra.api import deploy
from pyinfra.facts.server import Which

from server_files.hosts import load_servers


DOMAIN = "ilens-api.futurdevs.tech"
EMAIL = "phishink5@gmail.com"
CERT_FILE = f"/etc/letsencrypt/live/{DOMAIN}/fullchain.pem"
KEY_FILE = f"/etc/letsencrypt/live/{DOMAIN}/privkey.pem"
PEM_FILE = "/home/ubuntu/ilens.pem"


@deploy("Setup Server")
def setup_server():
    sudo = bool(host.get_fact(Which, "sudo"))
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
    # install snapd
    apt.packages(
        name="Install snapd",
        packages=["snapd"],
        _sudo=sudo,
    )


@deploy("Setup SSL Certificates")
def setup_ssl_certificates():
    sudo = bool(host.get_fact(Which, "sudo"))
    # install certbot
    server.shell(
        name="Install certbot",
        commands=[
            "snap install core; snap refresh core",
            "snap install --classic certbot",
        ],
        _sudo=sudo,
    )
    files.link(
        name="Link certbot to /usr/bin/certbot",
        path="/usr/bin/certbot",
        target="/snap/bin/certbot",
        force=True,
        _sudo=sudo,
    )
    # get SSL certificates
    server.shell(
        name="Get SSL certificates",
        commands=[
            f"certbot certonly --standalone -d {DOMAIN} -n --agree-tos -m {EMAIL}"
        ],
        _sudo=sudo,
    )
    # create pem file
    server.shell(
        name="Create pem file",
        commands=[
            f"cat {CERT_FILE} {KEY_FILE} > {PEM_FILE}",
            f"chmod 400 {PEM_FILE}",
        ],
        _sudo=sudo,
    )


@deploy("Setup HAProxy")
def setup_haproxy():
    servers = load_servers()["backend"]
    sudo = bool(host.get_fact(Which, "sudo"))
    setup_server()
    setup_ssl_certificates()
    apt.packages(
        name="Install HAProxy",
        packages=["haproxy"],
        _sudo=sudo,
    )
    files.template(
        name="Create haproxy.cfg",
        src="server_files/templates/haproxy.cfg.j2",
        dest="/etc/haproxy/haproxy.cfg",
        _sudo=sudo,
        domain=DOMAIN,
        cert_file=PEM_FILE,
        servers=servers,
    )
    systemd.service(
        name="Start HAProxy",
        service="haproxy",
        running=True,
        restarted=True,
        daemon_reload=True,
        _sudo=sudo,
    )


setup_haproxy()
