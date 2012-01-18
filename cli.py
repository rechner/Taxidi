#!/usr/bin/env python
#-*- coding:utf-8 -*-
# Parse out the log level and display usage if needed.
# parse() returns the specified log level.

import sys

def usage():
	print("usage: {} [--help] [--log=LEVEL]\n".format(sys.argv[0]))
	print("optional arguments:")
	print(" --help			Show this message and exit")
	print(" --log=LEVEL		Set the log verbosity to LEVEL\n")
	print("log levels:		DEBUG, INFO, WARNING, ERROR, CRITICAL\n")

def parse():
	levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICIAL']
	default = 'WARNING'
	if len(sys.argv) > 1:
		arg = sys.argv[1].split('=')
		if sys.argv[1] == '--help':
			usage()
			exit()
		elif arg[0] == "--log" and len(arg[1]) > 0:
				if arg[1].upper() in levels:
					print("Log level set to: {}".format(arg[1].upper()))
					return arg[1].upper()
				else:
					print("Bad log level")
					exit()
		else:
			print("Malformed argument")
			exit()
			
	return default

