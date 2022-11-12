#!/usr/bin/env python

import asyncio
import websockets
import logging

class Server:
    clients = set()

    def start(self):
        start_server = websockets.serve(self.ws_handler)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(start_server)
        loop.run_forever()

    async def stop(self):
        if self.clients:
            await asyncio.wait([client.close() for client in self.clients])
            [self.unregister(client) for client in self.clients]

    def register(self, ws):
        self.clients.add(ws)

    def unregister(self, ws):
        self.clients.remove(ws)

    async def send_to_clients(self, message):
        if self.clients:
            await asyncio.wait([client.send(message) for client in self.clients])

    async def ws_handler(self, ws, uri):
        self.register(ws)
        while True:
            try:
                await ws.recv()
            except websockets.exceptions.ConnectionClosed:
                self.unregister(ws)
                break

