#!/usr/bin/env python

import asyncio
import websockets
import logging

class Server:
    clients = set()

    def start(self):
        start_server = websockets.serve(self.ws_handler, "", 5001)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(start_server)
        loop.run_forever()

    async def stop(self):
        if self.clients:
            await asyncio.wait([client.close() for client in self.clients])
            [self.unregister(client) for client in self.clients]

    def register(self, ws):
        logging.debug("Registered client: %s", ws)
        self.clients.add(ws)

    def unregister(self, ws):
        logging.debug("Unregistered client: %s", ws)
        self.clients.remove(ws)

    def send_to_clients(self, message):
        logging.debug("Sending message %s", message)
        if self.clients:
            for client in self.clients:
                client.send(message)

    async def ws_handler(self, ws, uri):
        logging.debug("ws_handler")
        self.register(ws)
        while True:

