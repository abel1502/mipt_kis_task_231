import typing
import pathlib
import random


DEFAULT_WORDLIST = pathlib.Path(__file__).parent / "wordlists" / "default.txt"


def load_wordlist(path: pathlib.Path | str | None) -> "Wordlist":
    if path is None:
        path = DEFAULT_WORDLIST

    return Wordlist.parse(path)


class Wordlist:
    @staticmethod
    def parse(path: pathlib.Path | str) -> "Wordlist":
        if isinstance(path, str):
            path = pathlib.Path(path)
        assert path is not None

        def is_word_line(line: str) -> bool:
            line = line.split("#")[0]
            line = line.strip()

            return line.isalpha()

        with path.open("rt") as file:
            lines = tuple(filter(is_word_line, iter(file)))

        return Wordlist(lines)

    def __init__(self, words: typing.Iterable[str]):
        self._words: typing.Tuple[str] = tuple(words)

        assert len(self) > 0

    def __len__(self):
        return len(self._words)

    def rand_word(self) -> str:
        return random.choice(self._words)
