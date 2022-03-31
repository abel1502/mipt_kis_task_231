import typing
import asyncio
import textwrap
import random
import string

from . import network
from .network import BaseServerHandler
from .stream import Stream
from .wordlist import load_wordlist, Wordlist, pathlib


def run_server(addr: typing.Tuple[str, int],
               wordlist: "pathlib.Path" | str | None = None,
               attempts: int = 10):
    async def main():
        server = Server(load_wordlist(wordlist), attempts=attempts)

        await server.run(*addr)

    asyncio.run(main())


class Server(network.BaseServer):
    class Handler(network.BaseServerHandler):
        class UserExit(Exception):
            pass

        def __init__(self, server: "Server", attempts: int):
            super().__init__(server)

            self.attempts = attempts
            self.stream: Stream | None = None
            assert isinstance(self.server, Server)

        async def handle(self, stream: Stream) -> None:
            self.stream = stream

            try:
                await self.play()
            except (asyncio.IncompleteReadError, self.UserExit) as e:
                # noinspection SpellCheckingInspection
                self.server.log("Client {0[0]}:{0[1]} disconnected {1}",
                                self.stream.writer.get_extra_info("peername"),
                                "willingly" if isinstance(e, self.UserExit) else "unexpectedly")

        async def play(self) -> None:
            await self.greet()

            play_again = True
            while play_again:
                result = await self.play_round()

                await (self.win() if result else self.lose())

                play_again = await self.prompt_again()

        async def play_round(self) -> bool:
            lives: int = self.attempts
            word: str = typing.cast(Server, self.server).get_word()
            letters_left: typing.Set[str] = set(string.ascii_lowercase)
            letters_guessed: typing.Set[str] = set()

            while lives > 0:
                await self.say_word(word, letters_guessed)

                letter = await self.prompt_letter(iter(letters_left))

                if letter == '/':
                    raise self.UserExit()

                if letter not in letters_left:
                    await self.warn("You must chose one of the presented letters.\n"
                                    "To quit, type '/' (without the quotes)")
                    continue

                letters_left.remove(letter)

                assert letter not in letters_guessed

                if letter in word:
                    letters_guessed.add(letter)
                else:
                    lives -= 1

                if all(map(lambda c: c in letters_guessed, word)):
                    # The whole word was guessed
                    return True

            assert lives == 0

            # We're out of lives
            return False

        async def prompt_letter(self, letters_left: typing.Iterable[str]) -> str:
            await self.say(f"""
            The remaining letters are:
            {' '.join(letters_left)}
            """)

            resp = await self.ask("Type your letter (or '/' to exit):")

            return resp.lower()

        async def say_word(self, word: str, letters_guessed: typing.Set[str]) -> None:
            word = ''.join(map(lambda c: c if c in letters_guessed else '*', word))

            await self.say(f"""
            The word is: {word}
            """)

        async def warn(self, msg: str) -> None:
            pass

        async def say(self, msg: str) -> None:
            textwrap.dedent(msg).lstrip("\n")

            if not msg.endswith("\n"):
                msg += "\n"

            await self.stream.send(msg.encode())

        async def ask(self, prompt: str | None = None) -> str:
            if prompt is not None:
                await self.say(prompt + ":")

            await self.send_cmd("input")

            return (await self.stream.recv_line()).decode().rstrip("\r\n")

        async def send_cmd(self, cmd: str) -> None:
            await self.stream.send(f"\0{cmd}\n".encode())

        async def greet(self) -> None:
            await self.say(f"""
            Hello, and welcome to the Field of Wonders!
            The rules of this game are simple: you get a word,
            you try to guess it. You have {self.attempts} chances
            for mistake, then you're out! 
            """)

        async def win(self) -> None:
            await self.say(f"""
            Congratulations! You've won with {self.attempts} lives left! 
            {"This was a close one!" if self.attempts == 0 else "You're a pro!"}
            """)

        async def lose(self):
            await self.say("""
            Sorry, you lost... But good luck next time!
            """)

        async def prompt_again(self) -> True:
            MSGS = (
                "Wanna try again?",
                "How about another try?",
                "Let's go again!"
            )
            msg = random.choice(MSGS)

            await self.say(msg)
            resp = await self.ask("Type [Y]es or [n]o")
            resp = resp.strip().lower()

            return resp not in ("n", "no")

    verbose = True

    def __init__(self, wordlist: Wordlist, attempts: int = 10):
        super().__init__()

        self._wordlist: Wordlist = wordlist
        self._attempts: int = attempts

    def get_handler(self) -> BaseServerHandler:
        return self.Handler(self, self._attempts)

    def get_word(self) -> str:
        return self._wordlist.rand_word()


