#!/usr/bin/env python3

from . import Shell

import argparse
import sys


parser = argparse.ArgumentParser()

parser.add_argument('stdin', nargs='?', type=argparse.FileType('r'),
                    default=sys.stdin)
parser.add_argument('arguments', nargs=argparse.REMAINDER)

args = parser.parse_args()

shell = Shell(stdout=sys.stdout)

@shell.add_command
def stub(args):
    """
    Prints arguments as a python list
    """
    print(args)

stub.add_argument('args', nargs='*')


import inspect

@shell.add_command
def fail(exception):
    """
    Raise an exception
    """
    raise exception

fail.add_argument(
    'exception', nargs='?', default=Exception,
    choices=[member for name, member in inspect.getmembers(__builtins__)
             if isinstance(member, type) and issubclass(member, BaseException)
             and not issubclass(member, Warning)],
    type=lambda name:getattr(__builtins__, name))


shell.arguments = args.arguments

shell.send_stream(args.stdin)
