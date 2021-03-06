
import shlex
import sys
import traceback

from .environment import Environment
from .command import Command, List
from .stream import InputStream
from .parser import Parser


class HelpCommand(Command):
    def __init__(self, commands):
        self.commands = commands
        super().__init__(add_help=False, name='help')

    def run(self, command=None):
        if command is None:
            print('\n'.join(sorted(self.commands.keys())))
        else:
            try:
                parser = self.commands[command]
            except KeyError:
                print('No help available for unknown command {!r}'.format(
                    command))
                return
            parser.print_help()


class ExitCommand(Command):
    def __init__(self, **kwargs):
        super().__init__(add_help=False, name='exit')

    def run(self, status:int=0):
        """
        Terminate the shell process.
        """
        exit(status)


class EchoCommand(Command):
    def __init__(self, environment):
        super().__init__(name='echo')
        self.environment = environment

    def run(self, words:List(0)):
        """
        Print arguments to stdout
        """
        print(' '.join(word.format(**self.environment) for word in words))


def instantiate(class_or_object, *args, **kwargs):
    """
    Returns an instance of class_or_object.
    """
    if isinstance(class_or_object, type):
        return class_or_object(*args, **kwargs)
    else:
        return class_or_object


class Shell:
    def __init__(self, prompt='$ ', prompt2='> ', history=None,
                 use_rawinput=True, completekey='tab', stdout=sys.stdout,
                 parser=None, environment=Environment):
        self.parser = parser or Parser()
        self.stdout = stdout
        self.history = history
        self.use_rawinput = use_rawinput
        self.completekey = completekey
        self.environment = instantiate(environment)
        self.environment.update(
            prompt=prompt,
            prompt2=prompt2,
        )
        self.commands = dict()
        self.add_command(ExitCommand)
        self.add_command(HelpCommand(self.commands))
        self.add_command(EchoCommand(self.environment))

    def add_command(self, class_or_object=None):
        if class_or_object is None:
            def add_command(function):
                self.add_command(name, function)
                return function
            return add_command

        if isinstance(class_or_object, Command):
            instance = class_or_object
        elif (isinstance(class_or_object, type) and
              issubclass(class_or_object, Command)):
            instance = class_or_object()
        else:
            instance = Command(class_or_object)
        self.commands[instance.name] = instance
        return instance

    def get_prompt(self, continued):
        if continued:
            prompt = self.environment.get('prompt2', '')
        else:
            prompt = self.environment.get('prompt', '$ ')
        return prompt.format(**self.environment)

    def one_command(self, command, arguments):
        try:
            if command in self.commands:
                return self.commands[command](command, arguments)
            else:
                return self.default(command, arguments)
        except Exception as error:
            self.last_error = error
        else:
            self.last_error = None

    def default(self, command, arguments):
        print('No such command: {!r}'.format(command))

    def run_statements(self):
        for statement in self.parser:
            self.one_command(statement[0], statement[1:])

    def send_command(self, command):
        self.parser.send_line(command + '\n')
        self.run_statements()
        self.parser.__init__()

    def send_stream(self, stream):
        input_stream = InputStream(self, stream)
        try:
            for line in input_stream:
                self.parser.send_line(line)
                self.run_statements()
            if input_stream.isatty:
                input_stream.stdout.write('exit\n')
                input_stream.stdout.flush()
            self.commands['exit']('exit', [0])
        except KeyboardInterrupt:
            pass
        except SystemExit:
            raise
