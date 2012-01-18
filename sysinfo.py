#!/usr/bin/env python
#-*- coding:utf-8 -*-

# Written by Zac Sturgeon <admin@jkltech.net>

# Returns system information to be reported at the head of log file.
# Useful for debugging and simplifying error reporting.
# Attempts to use depreciated method platform.dist() for compatiblity
# with python prior to version 2.6.  Pass string=True to get OS as
# formatted string, otherwise False for tuple (default).

"""
Gets information about underlying operating system and python
interpreter using the platform module.
"""

import platform

def system(string=False):
    """
    Returns information about the OS in use.
    Pass string=True to get a formatted string, otherwise returns tuple.
    Works with Linux, Macintosh, Win32, and Java.  (Untested for UNIX)
    """
    
    # UNIX
    if platform.linux_distribution()[0]:    # (distname,version,id)
        try:
            os = platform.linux_distribution()
        except AttributeError:
            os = platform.dist()    # deprecated
        if string:  # return formatted, plus machine platform
            return "{1} {2} ({3}) on an {0}".format(machine(), *os)
        return os #otherwise return tuple
        
    # Macintosh
    if platform.mac_ver()[0]:       # (release, versioninfo, machine) 
        os = platform.mac_ver()     # versioninfo is a 3 string tuple   
        if string:
            #Version tuple is usually blank (why?) so leave it out
            return "{0} {1} {3}".format(platform.system(), *os)
        return os
                        
    # Win32
    if platform.win32_ver()[0]:
        os = platform.win32_ver()[:-1]  # remove useless last part
        if string: 
            return "{0} {1} {2} {3}".format(platform.system(), *os)
        return os
        
    # Java
    if platform.java_ver()[0]:
        os = platfrm.java_ver()
        if string: 
            return "{0} {1} {2} {3}".format(platform.system, *os)
        return os
        
def python(string=False):
    """
    
    Returns information about python instance.
    Pass string=True to get formatted string, otherwise returns tuple.
    (implementation, version, build, build date, compiler)
    
    """
    
    python = (  platform.python_implementation(),
                platform.python_version(),
                platform.python_build()[0],
                platform.python_build()[1],
                platform.python_compiler() )
    if string:
        return "{0} {1} {2} {3} ({4})".format(*python)
    return python
    
def machine():
    return platform.machine()
    

if __name__ == '__main__':
    print('OS is {0} on an {1}'.format(system(True), machine()))
    print('Python is {}'.format(python(True)))
