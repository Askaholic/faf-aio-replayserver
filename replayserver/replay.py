import asyncio
from replayserver.replaysender import ReplaySender
from replayserver.replayconnection import ReplayConnection
from replayserver.replaymerger import ReplayMerger


class Replay:
    def __init__(self):
        self._loop = asyncio.get_event_loop()
        self.stream = ReplayMerger(self._loop)
        self.sender = ReplaySender(self.stream, self._loop)

    def add_connection(self, connection):
        if connection.type == ReplayConnection.Type.READER:
            self.sender.add_reader(connection)
        elif connection.type == ReplayConnection.Type.WRITER:
            self.stream.add_writer(connection)
        else:
            raise ValueError("Invalid connection type")

    def close(self):
        self.stream.close()
        self.sender.close()

    async def wait_for_data_complete(self):
        await self.stream.wait_for_ended()

    async def wait_for_ended(self):
        await self.stream.wait_for_ended()
        await self.sender.wait_for_ended()
