import argparse
import field_of_wonders


def main_client(args):
    pass


def main_server(args):
    pass


def main():
    parser = argparse.ArgumentParser(
        description="The \"Field of Wonders\"-inspired server-based game of guessing words"
    )
    parser.add_argument("-m", "--mode", choices=("client", "server"), required=True)
    parser.add_argument("-a", "--addr", default=None)

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
