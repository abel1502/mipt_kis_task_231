import typing
import asyncio
import datetime

from . import network


def run_client(addr: typing.Tuple[str, int]):
    async def main():
        client = Client()

        await client.run(*addr)

    asyncio.run(main())


# Ideally this should have been inherited from an abstract class similar to BaseServer, but I hadn't had one in my lib,
# and creating one for a single project made little sense
class Client:
    verbose = True

    def __init__(self):
        self.stream: network.Stream | None = None

    async def run(self, host: str, port: int):
        async with await self._connect(host, port) as stream:
            self.stream = stream
            try:
                await self.loop()
            except (asyncio.IncompleteReadError, ConnectionError):
                self.log("Server disconnected")
            self.stream = None

            # Just in case. Should be done automatically
            stream.close()

    async def _connect(self, host: str, port: int) -> network.Stream:
        try:
            stream = await network.connect(host, port)
        except ConnectionRefusedError:
            self.log("Server refused connection")
            raise

        return stream

    async def loop(self):
        while True:
            cmd = await self.recv_cmd()
            await self.handle_cmd(cmd)

    async def recv_cmd(self) -> bytes:
        cmd = await self.stream.recv_line()
        cmd = cmd.rstrip(b"\r\n")
        return cmd

    async def handle_cmd(self, cmd: bytes) -> None:
        if cmd.startswith(b'\0'):
            await self.handle_control_cmd(cmd[1:].decode())
            return

        cmd = cmd.decode()
        print(cmd)

    async def handle_control_cmd(self, cmd: str) -> None:
        match cmd:
            case "input":
                # This call is blocking, but it's fine here, I assume
                data = input()
                await self.stream.send((data + '\n').encode())
            case _:
                self.log("Unknown control cmd received: {}", cmd)

    # noinspection PyMethodMayBeStatic
    def format_log_msg(self, msg: str) -> str:
        return "[CLIENT] [{time:%H:%M:%S}] {msg}".format(time=datetime.datetime.today(), msg=msg)

    def log(self, msg: str, *args, **kwargs):
        if not self.verbose:
            return

        msg = msg.format(*args, **kwargs)
        msg = self.format_log_msg(msg)
        self.write_msg(msg)

    # noinspection PyMethodMayBeStatic
    def write_msg(self, msg: str):
        print(msg)
