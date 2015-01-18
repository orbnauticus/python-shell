#!/usr/bin/env python3

from . import Shell, StubCommand

import argparse
import sys


parser = argparse.ArgumentParser()

args = parser.parse_args()

shell = Shell(stdout=sys.stdout)
shell.add_command('stub', StubCommand())
shell.send_stream(sys.stdin)
