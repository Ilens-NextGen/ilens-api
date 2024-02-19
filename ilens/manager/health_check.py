from pyinfra.api import deploy
from pyinfra.operations import server
from pyinfra import host


@deploy("Health Check")
def health_check():
    port = host.data.get("port", 8000)
    server.shell(
        name="Health Check",
        commands=[
            "echo 'Server is up'",
            (
                f"(curl 0:{port} | grep 200 > /dev/null && echo 'App is running "
                f"on port {port}...') || (echo 'App is down :(' && false)",
            ),
        ],
    )


health_check()
