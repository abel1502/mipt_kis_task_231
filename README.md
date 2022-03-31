# Task 231: Field of Wonders
This is the trial task for the MIPT KIS department.
The key point of this app is guessing a word letter-by-letter,
similar to the russian TV show "Field of Wonders"
(an analogue of the US "Wheel of Fortune").

## Requirements
 - Python 3.10

## Usage
To start the server, run `python3 run.py -m server --addr <host>:<port>`.
The default addr is `*:18071`.
You may also specify a custom wordlist via the `--wordlist <file>` option.

To start a client, run `python3 run.py -m client --addr <host>:<port>`,
where addr denotes the server's address, `localhost:18071` by default.

A more comprehensive overview of the available command line options
can be obtained by running `python3 run.py --help`.

## Copyright
Copyright © 2022 Andrew Belyaev. All rights reserved.
