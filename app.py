from sanic import Sanic
from sanic.response import text
from server.socket import server 

app = Sanic("Ilens")
server.attach(app)

@app.get("/")
async def hello_world(request):
    return text("Hello, world.")
