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
    print(args.args)

stub.add_argument('args', nargs='*')


shell.arguments = args.arguments

shell.send_stream(args.stdin)
