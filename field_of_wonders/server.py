import typing
import asyncio
import textwrap
import random
import string

from . import network
from .string_table import *
from .network import BaseServerHandler
from .stream import Stream
from .wordlist import load_wordlist, Wordlist, pathlib


class Strings:
    MSG_BAD_LETTER = res("You must chose one of the presented letters.\n"
                         "To quit, type '{key}' (without the quotes)")
    MSG_CORRECT = res("Correct!")
    MSG_WRONG = res("Sorry, wrong.")
    COUNT_CHANCES = plural("chance")
    COUNT_LIVES = plural("life", "lives")
    MSG_ATTEMPT_RESULT = res("{res} {chances} left")
    MSG_REMAINING_LETTERS = res("The remaining letters are:\n{}")
    MSG_TYPE_YOUR_LETTER = res("Type your letter (or '{key}' to exit)")
    MSG_WORD_IS = res("The word is: {word}")
    MSG_WORD_WAS = res("The word was: {word}")
    MSG_GREETINGS = res("""
        Hello, and welcome to the Field of Wonders!
        The rules of this game are simple: you get a word, you try to guess it.
        You have {chances} for mistake, then you're out!
        """)
    MSG_YOU_WON = res("Congratulations! You've won with {} left!\n{}")
    MSG_CLOSE_ONE = res("This was a close one!")
    MSG_YOU_PRO = res("You're a pro!")
    MSG_YOU_LOST = res("Sorry, you lost... But good luck next time!")
    MSGS_AGAIN = (
        res("Wanna try again?"),
        res("How about another try?"),
        res("Let's go again!"),
    )
    MSG_YES_OR_NO_DEF_YES = res("Type [Y]es or [n]o")
    WORD_YES = res("yes")
    WORD_NO = res("no")


def run_server(addr: typing.Tuple[str, int],
               wordlist: (pathlib.Path | str | None) = None,
               attempts: int = 10):
    async def main():
        server = Server(load_wordlist(wordlist), attempts=attempts)

        await server.run(host=addr[0], port=addr[1])

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

            peername = self.stream.writer.get_extra_info("peername")
            peername = "{0[0]}:{0[1]}".format(peername)

            self.server.log("Client connected from {}", peername)

            try:
                await self.play()
            except (asyncio.IncompleteReadError, ConnectionError, self.UserExit) as e:
                # noinspection SpellCheckingInspection
                self.server.log("Client {} disconnected {}", peername,
                                "voluntarily" if isinstance(e, self.UserExit) else "unexpectedly")
            else:
                self.server.log("Client {} disconnected in a very unexpected way", peername)

            # Is done automatically, but just in case
            stream.close()

        async def play(self) -> None:
            await self.greet()

            while True:
                await self.play_round()

                play_again = await self.prompt_again()
                if not play_again:
                    raise self.UserExit()

        async def play_round(self) -> None:
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
                    await self.warn(Strings.MSG_BAD_LETTER(key='/'))
                    continue

                letters_left.remove(letter)

                assert letter not in letters_guessed

                result_msg = ""
                if letter in word:
                    # Guessed
                    result_msg = Strings.MSG_CORRECT()
                    letters_guessed.add(letter)
                else:
                    # Not guessed
                    result_msg = Strings.MSG_WRONG()
                    lives -= 1

                await self.say(Strings.MSG_ATTEMPT_RESULT(res=result_msg,
                                                          chances=Strings.COUNT_CHANCES(lives)))

                if all(map(lambda c: c in letters_guessed, word)):
                    # The whole word was guessed
                    await self.win(word)
                    return

            assert lives == 0

            # We're out of lives

            await self.lose(word)

        async def prompt_letter(self, letters_left: typing.Iterable[str]) -> str:
            await self.say(Strings.MSG_REMAINING_LETTERS(' '.join(sorted(letters_left))))

            resp = await self.ask(Strings.MSG_TYPE_YOUR_LETTER(key='/'))

            return resp.lower()

        async def say_word(self, word: str,
                           letters_guessed: typing.Set[str] | None = None,
                           past: bool = True) -> None:
            if letters_guessed is not None:
                word = ''.join(map(lambda c: c if c in letters_guessed else '*', word))

            await self.say((Strings.MSG_WORD_IS if not past else Strings.MSG_WORD_WAS)(word=word))

        async def warn(self, msg: str) -> None:
            await self.say(msg)

        async def say(self, msg: str) -> None:
            msg = textwrap.dedent(msg).lstrip("\n")

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
            await self.say(Strings.MSG_GREETINGS(chances=Strings.COUNT_CHANCES(self.attempts)))

        async def win(self, lives: int, word: str | None = None) -> None:
            if word is not None:
                await self.say_word(word)

            await self.say(Strings.MSG_YOU_WON(lives=Strings.COUNT_LIVES(lives),
                                               secondary=(Strings.MSG_CLOSE_ONE() if
                                                          lives == 1 else
                                                          Strings.MSG_YOU_PRO())))

        async def lose(self, word: str | None = None):
            await self.say(Strings.MSG_YOU_LOST())
            if word is not None:
                await self.say_word(word, past=True)

        async def prompt_again(self) -> True:
            msg = random.choice(Strings.MSGS_AGAIN)()

            await self.say(msg)
            resp = await self.ask(Strings.MSG_YES_OR_NO_DEF_YES())
            resp = resp.strip().lower()

            NO = Strings.WORD_NO
            return resp not in (NO[0], NO)

    verbose = True

    def __init__(self, wordlist: Wordlist, attempts: int = 10):
        super().__init__()

        self._wordlist: Wordlist = wordlist
        self._attempts: int = attempts

    def get_handler(self) -> BaseServerHandler:
        return self.Handler(self, self._attempts)

    def get_word(self) -> str:
        return self._wordlist.rand_word()


