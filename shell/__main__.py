#!/usr/bin/env python3

from . import Shell

import argparse
import sys


parser = argparse.ArgumentParser()

args = parser.parse_args()

shell = Shell(stdout=sys.stdout)

@shell.add_command
def stub(args):
    """
    Prints arguments as a python list
    """
    print(args.args)

stub.add_argument('args', nargs='*', metavar='arg')

shell.send_stream(sys.stdin)
