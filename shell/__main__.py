#!/usr/bin/env python3

from . import Shell

import argparse
import sys


parser = argparse.ArgumentParser()

args = parser.parse_args()

shell = Shell(stdout=sys.stdout)
shell.send_stream(sys.stdin)
