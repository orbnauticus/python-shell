
import shlex
import sys
import traceback

from .environment import Environment
from .command import Command, Parser
from .stream import InputStream


class HelpCommand(Command):
    parser = Parser(add_help=False)

    parser.add_argument('command', nargs='?')

    def __init__(self, commands):
        self.commands = commands

    def run(self, args):
        if args.command is None:
            print('\n'.join(sorted(self.commands.keys())))
        else:
            try:
                command = self.commands[args.command]
            except KeyError:
                print('No help available for unknown command {!r}'.format(
                    args.command))
                return
            parser = getattr(command, 'parser', None)
            if parser is None:
                print('No help provided for {!r}'.format(args.command))
            else:
                if not parser.prog:
                    parser.prog = args.command
                parser.print_help()


class ExitCommand(Command):
    parser = Parser(add_help=False)
    parser.add_argument(
        'status', type=int, nargs='?', default=0,
        help="The return code of the process. Default is 0")

    def run(self, args):
        """
        Terminate the shell process.
        """
        exit(args.status)


class StubCommand(Command):
    def run(self, args):
        print(args)


class Shell:
    def __init__(self, prompt='$ ', prompt2='> ', history=None,
                 use_rawinput=True, completekey='tab', stdout=sys.stdout):
        self.stdout = stdout
        self.history = history
        self.use_rawinput = use_rawinput
        self.completekey = completekey
        self.environment = Environment(
            prompt=prompt,
            prompt2=prompt2,
        )
        self.commands = dict()
        self.add_command('exit', ExitCommand())
        self.add_command('help', HelpCommand(self.commands))

    def parser(self, line):
        try:
            return (shlex.split(line, comments=True), '')
        except ValueError as error:
            if error.args == ('No closing quotation',):
                return None, line
            elif error.args == ('No escaped character',):
                return None, line[:-1]
            else:
                raise

    def add_command(self, name, class_):
        self.commands[name] = class_

    def get_prompt(self, continued):
        if continued:
            prompt = self.environment.get('prompt2', '')
        else:
            prompt = self.environment.get('prompt', '$ ')
        return prompt.format(**self.environment)

    def one_command(self, command, arguments):
        if command in self.commands:
            self.commands[command](command, arguments)
        else:
            self.default(command, arguments)

    def default(self, command, arguments):
        print('No such command: {!r}'.format(command))

    def send_command(self, command):
        raise NotImplementedError

    def send_stream(self, stream):
        input_stream = InputStream(self, stream)
        try:
            for command, arguments in input_stream:
                self.one_command(command, arguments)
            if input_stream.isatty:
                input_stream.stdout.write('exit\n')
                input_stream.stdout.flush()
            self.commands['exit']('exit', [0])
        except KeyboardInterrupt:
            pass
        except SystemExit:
            raise
