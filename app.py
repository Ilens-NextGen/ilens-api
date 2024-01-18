from sanic import Sanic
from sanic.response import text


class ILens(Sanic):
    """The ILens API server."""


app = ILens("Ilens")


@app.get("/")
async def hello_world(request):
    return text("Hello, world.")


def create_app():
    from server.socket import server

    server.attach(app)
    return app
