import argparse
import typing
from urllib.parse import urlparse
import sys

import field_of_wonders


DEFAULT_PORT = 18071
DEFAULT_ATTEMPTS = 5


def parse_addr(addr: str | None, default: str) -> typing.Tuple[str, int]:
    error = ValueError("Invalid address format")

    if addr is None:
        addr = default

    try:
        addr = urlparse(addr, allow_fragments=False)
    except ValueError as e:
        raise error from e

    should_be_empty = (addr.scheme, addr.path, addr.query)
    if not all(map(lambda x: x == "", should_be_empty)):
        raise error

    should_be_none = (addr.username, addr.password)
    if not all(map(lambda x: x is None, should_be_none)):
        raise error

    host, port = addr.hostname, addr.port
    if not host or not port:
        raise error

    return host, port


def main_client(args):
    addr = parse_addr(args.addr, default=f"localhost:{DEFAULT_PORT}")

    field_of_wonders.run_client(addr)


def main_server(args):
    addr = parse_addr(args.addr, default=f"*:{DEFAULT_PORT}")
    wordlist = args.wordlist
    attempts = args.attempts

    field_of_wonders.run_server(addr, wordlist=wordlist, attempts=attempts)


def main():
    assert sys.version_info >= (3, 10), "Python 3.10 required"

    parser = argparse.ArgumentParser(
        description="The \"Field of Wonders\"-inspired server-based game of guessing words"
    )
    parser.add_argument("-m", "--mode", choices=("client", "server"), required=True)
    parser.add_argument("-a", "--addr", default=None,
                        help="The address the client would connect to, or the server would bind to")
    parser.add_argument("--wordlist", default=None,
                        help="The custom wordlist for the server")
    parser.add_argument("--attempts", default=DEFAULT_ATTEMPTS, type=int,
                        help="The number of failed attempts allowed by the server")

    args = parser.parse_args()

    match args.mode:
        case "client":
            main_client(args)
        case "server":
            main_server(args)
        case _:
            assert False


if __name__ == "__main__":
    main()
