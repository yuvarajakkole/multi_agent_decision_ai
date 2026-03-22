# backend/websocket_server.py

import uvicorn

from config.settings import API_HOST, API_PORT


def start():

    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        ws="websockets"
    )


if __name__ == "__main__":

    start()