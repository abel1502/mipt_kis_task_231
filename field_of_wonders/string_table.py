import typing
from typing import Any


def plural(word_single: str, word_plural: str | None = None):
    def getter(number: int):
        nonlocal word_single
        nonlocal word_plural

        if word_plural is None:
            word_plural = word_single + "s"

        last_digit = number % 10
        second_digit = number / 10 % 10

        word = word_plural
        if second_digit != 1 and last_digit == 1:
            word = word_single

        return f"{number} {word}"

    return getter


def res(value: str):
    def getter(*args, **kwargs):
        if not args and not kwargs:
            return value
        return value.format(*args, **kwargs)

    return getter


__all__ = ("res", "plural")
