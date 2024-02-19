from pyinfra.api import deploy
from pyinfra.operations import server
from pyinfra import host


@deploy("Health Check")
def health_check():
    port = host.data.get("port", 8000)
    server.shell(name="Server is up?", commands=["true"])
    server.shell(
        name=f"Running on port {port}?",
        commands=[f"curl 0:{port} -sI > /dev/null || false"],
    )


health_check()
