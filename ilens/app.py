from pathlib import Path
from sanic import Sanic
from sanic.response import text
from ilens.server.settings import SERVER_ID
from sanic.response import file_stream
from sanic.exceptions import NotFound
from aiofiles import os

BASE_DIR = Path(__file__).parent


class ILens(Sanic):
    """The ILens API server."""


app = ILens("Ilens")


@app.get("/")
async def hello_world(request):
    return text(f"Hello, World! from {SERVER_ID}")


@app.get("/resource/<filename>")
async def get_resource(request, filename: str):
    location = BASE_DIR / "uploads" / filename
    if await os.path.exists(location):
        file_size = (await os.stat(location)).st_size
        headers = {"Content-Length": str(file_size)}
        return await file_stream(location, chunk_size=1024, headers=headers)
    else:
        raise NotFound("File not found")


def create_app():
    from ilens.server.socket import server

    server.attach(app)
    return app
