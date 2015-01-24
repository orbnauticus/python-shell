#!/usr/bin/env python3

from . import Shell
from .command import Parameter, List

import argparse
import sys


parser = argparse.ArgumentParser()

parser.add_argument('stdin', nargs='?', type=argparse.FileType('r'),
                    default=sys.stdin)
parser.add_argument('arguments', nargs=argparse.REMAINDER)

args = parser.parse_args()

shell = Shell(stdout=sys.stdout)

@shell.add_command
def stub(args:List(1)):
    """
    Prints arguments as a python list
    """
    print(list(args))


import inspect


class Error(Parameter):
    exceptions = dict(
        (name, member) for name, member in inspect.getmembers(__builtins__)
        if isinstance(member, type) and issubclass(member, BaseException)
        and not issubclass(member, Warning))

    def __call__(self, value):
        return value

    def add_to(self, parameter, command):
        command.add_argument(
            parameter.name, choices=self.exceptions.keys(), nargs='?',
            default=parameter.default,
            type=lambda name:getattr(__builtins__, name))


@shell.add_command
def fail(exception:Error()=Exception):
    """
    Raise an exception
    """
    raise exception


shell.arguments = args.arguments

shell.send_stream(args.stdin)
