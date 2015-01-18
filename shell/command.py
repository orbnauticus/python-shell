
from argparse import ArgumentParser


class Parser(ArgumentParser):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('prog', '')
        super().__init__(*args, **kwargs)


class Command:
    def __init__(self, function=None):
        if function is not None:
            self.run = function
        parser = getattr(self, 'parser', None)
        if parser and not parser.description:
            parser.description = self.run.__doc__

    def __call__(self, command, arguments):
        parser = getattr(self, 'parser', None)
        if parser is not None:
            if not parser.prog:
                parser.prog = command
            try:
                arguments = self.parser.parse_args(arguments)
            except SystemExit:
                return
        self.run(arguments)
