
import os
import shlex

try:
    import readline
except ImportError:
    readline = None


class InputStream:
    def __init__(self, shell, stdin):
        self.stdin = stdin
        self.stdout = shell.stdout
        self.parser = shell.parser
        self.get_prompt = shell.get_prompt
        self.use_rawinput = shell.use_rawinput
        self.completekey = shell.completekey
        self.isatty = stdin.isatty()
        self.history = shell.history and os.path.expanduser(shell.history)

    def complete(self, text, state):
        pass

    def __enter__(self):
        if readline and self.use_rawinput and self.completekey:
            self.old_completer = readline.get_completer()
            readline.set_completer(self.complete)
            readline.parse_and_bind(self.completekey + ": complete")
            if self.history:
                try:
                    readline.read_history_file(self.history)
                except FileNotFoundError:
                    pass

    def __exit__(self, exc, obj, tb):
        if exc is EOFError:
            return True
        if readline and self.use_rawinput and self.completekey:
            readline.set_completer(self.old_completer)
            if self.history:
                readline.write_history_file(self.history)

    def readline(self, continued):
        prompt = self.get_prompt(continued) if self.isatty else ''
        if self.use_rawinput:
            return '%s\n%s' % (continued, input(prompt))
        else:
            if self.isatty:
                self.stdout.write(prompt)
                self.stdout.flush()
            line = self.stdin.readline()
            if not len(line):
                raise EOFError
            return '%s\n%s' % (continued, line.rstrip('\r\n'))

    def __iter__(self):
        with self:
            excess = ''
            while True:
                statement, excess = self.parser(self.readline(excess))
                if statement:
                    yield statement[0], statement[1:]
