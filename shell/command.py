
from argparse import ArgumentParser


class Parser(ArgumentParser):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('prog', '')
        super().__init__(*args, **kwargs)


class Command:
    def __init__(self, function=None):
        if function is not None:
            self.run = function

    def __call__(self, command, arguments):
        if self.parser is not None:
            try:
                arguments = self.parser.parse_args(arguments)
            except SystemExit:
                return
        self.run(arguments)
