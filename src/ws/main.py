import asyncio
from typing import Set, Any
import websockets
from websockets.legacy.server import WebSocketServerProtocol

class ChatServer:
    def __init__(self, host: str = "localhost", port: int = 8080) -> None:
        self.host: str = host
        self.port: int = port
        self.clients: Set[WebSocketServerProtocol] = set()

    async def handler(self, websocket: Any) -> None:
        self.clients.add(websocket)
        print(f"Client connected: {websocket.remote_address}")
        try:
            async for message in websocket:
                for client in self.clients:
                    if client.open:
                        if client == websocket:
                            await client.send("You: " + message)
                        else:
                            await client.send(message)
        except websockets.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            print(f"Client disconnected: {websocket.remote_address}")

    async def start(self) -> None:
        """Start the WebSocket server."""
        print(f"Chat server running on ws://{self.host}:{self.port}")
        async with websockets.serve(self.handler, self.host, self.port):
            await asyncio.Future()  # run forever


if __name__ == "__main__":
    server = ChatServer()
    asyncio.run(server.start())