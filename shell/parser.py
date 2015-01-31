#!/usr/bin/env python3

from collections import deque


class Singleton:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


EMIT_STATEMENTS = Singleton('EMIT_STATEMENTS')
END_STATEMENT = Singleton('END_STATEMENT')
END_TOKEN = Singleton('END_TOKEN')
INCLUDE = Singleton('INCLUDE')
END_CONTEXT = Singleton('END_CONTEXT')
REVISIT = Singleton('REVISIT')


class Context:
    def __init__(self, directives):
        self.directives = dict(
            (key, value if isinstance(value, list) else [value])
            for key, value in directives.items())
        self.directives.setdefault(None, [INCLUDE])


class Comment(Context):
    def __init__(self, final, revisit=False):
        super().__init__({
            final: [END_CONTEXT] + ([REVISIT] if revisit else []),
            None: [''],
        })


class StrictQuote(Context):
    def __init__(self, final):
        super().__init__({
            final: END_CONTEXT,
        })


class Quote(StrictQuote):
    def __init__(self, final):
        super().__init__(final)
        self.directives.update({
            '\\': [Escape('\\', {
                final: final,
                None: ['\\', INCLUDE],
            })],
        })


class Escape(Context):
    def __init__(self, escape, directives):
        directives.setdefault(None, INCLUDE)
        directives.setdefault(escape, INCLUDE)
        super().__init__(directives)
        for key in self.directives:
            value = self.directives[key]
            if value[-1] != END_CONTEXT:
                value.append(END_CONTEXT)


class GeneralContext(Context):
    def __init__(self):
        super().__init__({
            '"': Quote('"'),
            "'": StrictQuote("'"),
            '#': Comment('\n', True),
            ' ': END_TOKEN,
            '\t': END_TOKEN,
            '\r': END_TOKEN,
            '\\': Escape('\\', {
                '\n': '',
                None: INCLUDE,
            }),
            '\n': EMIT_STATEMENTS,
            ';': EMIT_STATEMENTS,
        })


class Parser:
    def __init__(self):
        self.token = ''
        self.buffer = ''
        self.statement = []
        self.statements = []
        self.newline = '\n'
        self.context_stack = deque()
        self.context_stack.append(GeneralContext())

    @property
    def context(self):
        return self.context_stack[-1]

    def send_line(self, line):
        self.buffer = self.buffer + line.rstrip('\r\n') + self.newline

    def is_complete(self):
        return not (self.token or self.statement or self.statements)

    def _handle_character(self, character):
        directives = self.context.directives[
            character if character in self.context.directives else None]
        for directive in directives:
            if isinstance(directive, str):
                # print('** append %r' % directive)
                self.token += directive
            elif isinstance(directive, Context):
                # print('** push context %r' % directive)
                self.context_stack.append(directive)
            elif directive is END_CONTEXT:
                # print('** pop context %r' % self.context)
                self.context_stack.pop()
            elif directive is INCLUDE:
                # print('** include %r' % character)
                self.token += character
            elif directive is REVISIT:
                # print('** revisit %r' % character)
                result = self._handle_character(character)
                if result is not None:
                    return result
            elif isinstance(directive, Exception):
                raise directive
            elif directive in (END_TOKEN, END_STATEMENT, EMIT_STATEMENTS):
                # print(directive)
                return directive

    def __iter__(self):
        count = 0
        for count, character in enumerate(self.buffer, 1):
            new = self._handle_character(character)
            if new in (END_TOKEN, END_STATEMENT):
                assert len(self.context_stack) == 1
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

    import inspect

    def test_statement(statement, *expected):
        callingframe = inspect.getouterframes(inspect.currentframe())[-1]
        _, filename, linenumber, _, _, _ = callingframe
        parser = Parser()
        parser.send_line(statement.strip('\n') + '\n')
        if not parser.is_complete():
            print('*' * 40)
            print('Incomplete statement at line {} of {}:'.format(
                linenumber, filename))
            print('\t$', '\n\t> '.join(statement.split('\n')))
            return
        expected = list(expected)
        got = list(parser)
        if got != expected:
            print('*' * 40)
            print('Statement at line {} of {}:'.format(linenumber, filename))
            print('\t$', '\n\t> '.join(statement.split('\n')))
            print('Expected:')
            print('\n'.join('\t{!r}'.format(x) for x in expected))
            print('Got:')
            print('\n'.join('\t{!r}'.format(x) for x in got))
            return

    test_statement('stub', ['stub'])
    test_statement('stub 1 2 3', ['stub', '1', '2', '3'])
    test_statement('stub 1 2 \\\n3', ['stub', '1', '2', '3'])
    test_statement('stub "1\n2 3"', ['stub', '1\n2 3'])
    test_statement('stub 1\\n2 3', ['stub', '1n2', '3'])
    test_statement('stub "1\n2" 3', ['stub', '1\n2', '3'])
    test_statement('stub 1 ; stub 2', ['stub', '1'], ['stub', '2'])
    test_statement('stub 1; stub 2;;;', ['stub', '1'], ['stub', '2'])
    test_statement('stub "1 2 3"', ['stub', '1 2 3'])
    test_statement('stub "1 \'2\' 3"', ['stub', "1 '2' 3"])
    test_statement(
        'stub "1 2 3" # This comment is ignored through the end of the line',
        ['stub', '1 2 3'])
    test_statement('stub "1 2 3 # This comment is part of the string\n"',
                   ['stub', '1 2 3 # This comment is part of the string\n'])
    test_statement(r'stub 1\ 2\ 3', ['stub', '1 2 3'])
    test_statement(r'stub \z', ['stub', 'z'])
    test_statement(r'stub "\z"', ['stub', r'\z'])
