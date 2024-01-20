from sanic import Sanic
from sanic.response import text
from server.settings import SERVER_ID


class ILens(Sanic):
    """The ILens API server."""


app = ILens("Ilens")


@app.get("/")
async def hello_world(request):
    return text(f"Hello, World! from {SERVER_ID}")


def create_app():
    from server.socket import server

    server.attach(app)
    return app
