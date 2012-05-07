#!/usr/bin/env python
#-*- coding:utf-8 -*-

# Taxídí (http://jkltech.net/taxidi)
# Copyright 2010-2011 © Zac Sturgeon <admin@jkltech.net>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.

import cli
import time
import logging, logging.handlers
import sysinfo

logFile = 'error.log'  #send this somewhere else for production (/tmp/?)
loglevel = cli.parse()

#TODO: Fix logging.  For now the following code puts log on the console:
#~ self.log = logging.getLogger(__name__)
#~ self.log.setLevel(logging.DEBUG)
#~ ch = logging.StreamHandler()
#~ ch.setLevel(logging.DEBUG)
#~ formatter = logging.Formatter('[%(asctime)s] %(module)-6s  [%(levelname)-8s]  %(message)s')
#~ ch.setFormatter(formatter)
#~ self.log.addHandler(ch)

#set up local file logging
logging.basicConfig(filename=logFile, filemode='a',
    format='[%(asctime)s] %(module)-6s  [%(levelname)-8s]  %(message)s',
    level=getattr(logging, loglevel.upper()))

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.debug('\n')
logger.debug('Logger started at {}'.format(time.ctime()))
logger.debug('Logging started with format [time] (module) [level] message...')

# print system information later error reporting and debugging
logger.info('Operating System is {}'.format(sysinfo.system(True)))
logger.info('Environment is {}'.format(sysinfo.python(True)))

# create console handler (show messages on stdout)
ch = logging.StreamHandler()
ch.setLevel(getattr(logging, loglevel.upper()))
logger.debug('Set console logger level to {}'.format(loglevel.lower()))

# create formatter
formatter = logging.Formatter('%(module)-7s %(levelname)-8s   %(message)s')
ch.setFormatter(formatter)  # add formatter to ch
logger.addHandler(ch)       # add ch to logger

# 'application' code
#logger.debug('debug message')
#logger.info('info message')
#logger.warn('warn message')
#logger.error('error message')
#logger.critical('critical message')

import conf     #import settings for application and database
                #~ #do this first?  (for logfile settings?)

if conf.config['database']['driver'].lower() == 'sqlite':
    import dblib.sqlite as sqlite
    try:
        logger.debug('Attempting to open datbase object.')
        db = sqlite.Database(conf.homeAbsolutePath(conf.config['database']['file']))
    except TypeError as e:
        logger.error('({0})'.format(e))
        logger.critical('Unable to open database (file write-protected?)')
        #display an error dialogue and exit
        exit()
else:
    logger.error('Database driver not implemented: {0}'. \
        format(conf.config['database']['driver']))



#~ db.Register("Zac", "Sturgeon", "1993-05-13", "3174555832", "V-5832", "Blah")
#~ a = db.GetAll()
#~ for record in a:
    #~ print record[1]+' '+record[2]
#~


import webcam
store = webcam.Storage()


exit()
