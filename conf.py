#!/usr/bin/env python
#-*- coding:utf-8 -*-

# Read config.ini from the present working directory

import os.path, sys
import configobj
import logging

appPath = os.path.abspath(os.path.dirname(os.path.join(sys.argv[0])))
inifile = os.path.join(appPath, 'config.ini')

logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)
logger.info("Reading configuration from '{}'".format(inifile))
