from pyinfra.api import deploy, FactBase
from pyinfra import host


class ServerUp(FactBase):
    @staticmethod
    def command():
        port = host.data.get("port", 8000)
        return f"curl 0.0.0.0:{port} -sI || true"

    def process(self, output):
        for line in output:
            if "200 OK" in line:
                return True
        return False


class SocketioUp(FactBase):
    @staticmethod
    def command():
        port = host.data.get("port", 8000)
        return f"curl 0.0.0.0:{port}/socket.io -sI || true"

    def process(self, output):
        for line in output:
            if "400 Bad Request" in line:
                return True
        return False


@deploy("Health Check")
def health_check():
    # print(host.get_fact(ServerUp))
    # print(host.get_fact(SocketioUp))
    if not host.get_fact(ServerUp):
        raise Exception("Server is not up")
    if not host.get_fact(SocketioUp):
        raise Exception("Socketio is not up")


health_check()
