#!/usr/bin/env python3


class Singleton:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


EMIT_STATEMENTS = Singleton('EMIT_STATEMENTS')
END_STATEMENT = Singleton('END_STATEMENT')
END_TOKEN = Singleton('END_TOKEN')


class Context:
    def __init__(self, escape=False, quote='', comment=''):
        self.escape = escape
        self.quote = quote
        self.comment = comment

    def assert_clean(self):
        assert all(bool(x) is False for x in vars(self).values())


class Classes:
    def __init__(self, whitespace=' \t\r\n', terminator='\n;', escape='\\'):
        self.whitespace = whitespace
        self.operators = {
            '\n': EMIT_STATEMENTS,
            ';': END_STATEMENT,
        }
        self.escape = escape
        self.quotes = {
            '"': '"',
            "'": "'",
        }
        self.newline = '\n'
        self.sequences = {
            '\n': '',
            't': '\t',
            'r': '\r',
            'n': '\n',
            ' ': ' ',
        }
        self.comments = {
            '#': '\n',
        }


class Parser:
    def __init__(self):
        self.token = ''
        self.buffer = ''
        self.statement = []
        self.statements = []
        self.context = Context()
        self.classes = Classes()

    def send_line(self, line):
        self.buffer = self.buffer + line.rstrip('\r\n') + self.classes.newline

    def is_complete(self):
        return not (self.token or self.statement or self.statements)

    def _include(self, character):
        self.token += character
        if self.context.escape:
            self.context.escape = False

    def _ignore(self):
        self.context.escape = False

    def _handle_character(self, character):
        if self.context.comment:
            if character == self.context.comment:
                self.context.comment = ''
                if character == self.classes.newline:
                    return self._handle_character(self.classes.newline)
        elif self.context.escape:
            if character in self.classes.sequences:
                self._include(self.classes.sequences[character])
            else:
                self._include(self.classes.escape + character)
        elif character == self.classes.escape:
            self.context.escape = True
        elif self.context.quote:
            if character == self.context.quote:
                self.context.quote = ''
            else:
                self._include(character)
        elif character in self.classes.operators:
            return self.classes.operators[character]
        elif character in self.classes.quotes:
            self.context.quote = self.classes.quotes[character]
        elif character in self.classes.comments:
            self.context.comment = self.classes.comments[character]
        elif character in self.classes.whitespace:
            return END_TOKEN
        else:
            self._include(character)

    def __iter__(self):
        count = 0
        for count, character in enumerate(self.buffer, 1):
            new = self._handle_character(character)
            if new in (END_TOKEN, END_STATEMENT):
                self.context.assert_clean()
            if (new in (END_TOKEN, END_STATEMENT, EMIT_STATEMENTS)
                    and self.token):
                self.statement.append(self.token)
                self.token = ''
            if new in (END_STATEMENT, EMIT_STATEMENTS) and self.statement:
                self.statements.append(self.statement)
                self.statement = []
            if new is EMIT_STATEMENTS and self.statements:
                for statement in self.statements:
                    yield statement
                self.statements = []
        self.buffer = self.buffer[count:]

if __name__ == '__main__':

    from io import StringIO

    sample = StringIO(r"""
stub
stub 1 2 3
stub 1 2 \
3
stub "1
2 3"
stub 1\n2 3
stub "1\n2" 3
stub 1 ; stub 2
stub 1; stub 2;;;
stub "1 2 3"
stub "1 '2' 3"
stub "1 2 3" # This comment is ignored through the end of the line
stub "1 2 3 # This comment is part of the string
"
stub 1\ 2\ 3
stub \z

""")

    parser = Parser()

    for line in sample:
        parser.send_line(line)
        print('** buffer %r' % parser.buffer)
        for statement in parser:
            print(repr(statement))
    if parser.buffer:
        print('** Leftover buffer %r' % parser.buffer)
