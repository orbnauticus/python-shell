
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
        if self.use_rawinput:
            return input(self.get_prompt(continued) if self.isatty else '')
        else:
            if self.isatty:
                self.stdout.write(self.get_prompt(continued))
                self.stdout.flush()
            line = self.stdin.readline()
            if not len(line):
                raise EOFError
            return line.rstrip('\r\n')

    def __iter__(self):
        with self:
            multiline = ''
            while True:
                line = self.readline(multiline)
                if multiline:
                    line = '%s\n%s' % (multiline, line)
                multiline = ''
                try:
                    words = shlex.split(line, comments=True)
                except ValueError as error:
                    if error.args == ('No closing quotation',):
                        multiline = line
                        continue
                    elif error.args == ('No escaped character',):
                        multiline = line[:-1]
                        continue
                    else:
                        raise
                if not words:
                    continue
                yield words[0], words[1:]
