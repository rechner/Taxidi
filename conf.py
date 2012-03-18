#!/usr/bin/env python
#-*- coding:utf-8 -*-

# Read config.ini from the present working directory
# values are read out section-at-a-time using in-house methods for convenience,
# but can also be read outside the module.

import os.path, sys
import configobj
import logging

appPath = os.path.abspath(os.path.dirname(os.path.join(sys.argv[0])))
inifile = os.path.join(appPath, 'config.ini')

logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)
logger.info("Reading configuration from '{0}'".format(inifile))
config = configobj.ConfigObj(inifile)

def as_bool(string):
    """Returns True if the key contains a string that represents True, or is the True object.
Returns False if the key contains a string that represents False, or is the False object.
Raises a ValueError if the key contains anything else.

Strings that represent True are not case sensitive, and include: true, yes, on, 1.
(I couldn't get configobj's built in as_bool function to work. ~~Zac 24.02.2012) 
    """
    #true, yes, on, 1
    try: #is it a string?
        test = string.lower() # ignore the case.
    except AttributeError:    # is an object, not string.
        return bool(test)     # return bool value.
    
    if test == 'true' or test == 'yes' or test == 'on' or test == '1d':
        return True
    elif test == 'false' or test == 'no' or test == 'off' or test == '0':
        return False
    else:
        raise ValueError('Mangled boolean representation "{0}"'.format(string))
        
# Read section.  Returns values as a converted list.
def conf():
    config['general']

def main():
    # read out configuration for debugging... and stuff.
    pass

if __name__ == "__main__":
    main()
