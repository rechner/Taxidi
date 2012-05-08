#!/usr/bin/env python
#-*- coding:utf-8 -*-

# Read config.ini from the present working directory, or from ~/.taxidi/ if a
# local config doesn't exist (default behaviour).  Values are read
# through `object`.
# If ~/.taxidi/resources/ doesn't exist,  it is created with what's in pwd.
# Everything just happens on import.

#TODO: (HIGH DEADLINE 03.05) Implement basic theme files.
#TODO: Create database folders in ~/.taxidi/ for first run

#TODO: Implement fetch config from http(s) or sftp.
#TODO: Implement validation.

"""
Example:

import conf
configHandler = conf.Config()
if configHandler.status == conf.CREATED_NEW:
    #show warning and/or first run dialogue.
elif configHandler.status == conf.ERROR_NOT_WRITEABLE:
    #show error dialogue & quit.
    print "ERROR: Could not write new config at %s." % conf.inifile

#read a value:
print conf.object['database']['driver']

#write a value:
conf.object['database']['username'] = 'foo'
conf.object['interface']['fullscreen'] = True
conf.write()
"""

import os, sys
import shutil
import configobj
import logging

#Constants:
CREATED_NEW = 1  #Signal that A new config file was created. (First run dialogue, etc.)
ERROR_NOT_WRITEABLE = 2  #The destination couldn't be written to.

global homepath
homepath = os.getenv('USERPROFILE') or os.getenv('HOME')

class Config:
    def __init__(self):

        self.log = logging.getLogger(__name__)
        #~ self.log.setLevel(logging.DEBUG)
        self.homepath = homepath
        pwd = os.path.abspath(os.path.dirname(os.path.join(sys.argv[0])))
        share = pwd  #for now.  Future: /usr/share/taxidi/ (UNIX) AppData folder (WIN32)

        #Try to read from present directory first:
        inifile = os.path.join(pwd, 'config.ini')
        self.log.debug('Trying local config path {0}...'.format(inifile))
        try:
            f = open(inifile)
            f.close()
        except IOError:
            self.log.debug('No config.ini in present working directory.')

            #Try to read from home folder instead:
            appPath = os.path.join(self.homepath, '.taxidi')
            inifile = os.path.join(appPath, 'config.ini')
            self.log.debug('Trying config path {0}...'.format(appPath))
            try: #See if file exists
                _f = open(inifile)
                _f.close()
            except IOError as _e:
                self.log.warning("Configuration doesn't exist.")
                self.log.error(_e)

                if not os.path.exists(appPath): #Check if ~/.taxidi/ exists.
                    self.log.warning("Local path didn't exist.  Creating with default values...")
                    try:
                        os.makedirs(appPath)  #Create application settings folder
                    except error as _e:
                        self.log.error(_e)

                #create the config by copying template from localdir.
                #(may change to /usr/share/taxidi/ for distribution(?))
                self.log.debug('Creating default configuration....')
                try:
                    shutil.copyfile(os.path.join(pwd, 'config.ini.template'), inifile)
                    self.log.debug('Created config at {0}'.format(inifile))
                    self.status = CREATED_NEW
                except IOError as _e:
                    self.log.error(_e)
                    self.log.error('is destination writeable?')
                    self.status = ERROR_NOT_WRITEABLE

            resourcesPath = os.path.join(self.homepath,
                '.taxidi', 'resources')
            _resources = ['nametag', 'themes']  #folders to check for/copy
            for _folder in _resources:
                if not os.path.exists(_folder):
                    #Home doesn't exist: copy them:
                    try:
                        self.log.debug('Copying {0} resources from {1} to {2}...'
                            .format(_folder, share, resourcesPath))
                        shutil.copytree(os.path.join(share, 'resources', _folder),
                            os.path.join(resourcesPath, _folder))
                    except shutil.Error as _e:
                        self.log.error(_e)
                        self.log.error('Error while copying resource.')
                    except os.error as _e:
                        if _e.errno == 17:
                            self.log.warning('Lower tree directory exists.')
                        else:
                            self.log.error(_e)

        self.log.info("Reading configuration from '{0}'".format(inifile))
        self.config = configobj.ConfigObj(inifile, encoding='utf-8')

#Read the default theme:
class Theme:
    def __init__(self, path=homepath):
        """
        Handles reading of theme files.
        """
        self.directory = os.path.join(os.path.abspath(path), 'resources', 'themes')
        self.log = logging.getLogger(__name__)
        #~ self.directory = os.path.join(pwd

    def listThemes(self):
        try:
            resource = os.listdir(self.directory)
        except OSError as e:
            self.log.error('({0})'.format(e))
            return []

        themes = []
        #Remove any files from themes[] that are not directories:
        for i in resource:
            if os.path.isdir(os.path.join(self.directory, i)):
                themes.append(i)

        valid = []
        #Check that each folder has the corresponding .conf file:
        for i in themes:
            if os.path.isfile(os.path.join(self.directory, i, 'theme.conf')):
                valid.append(i)

        valid.sort()
        del resource, themes
        self.log.debug("Found templates {0}".format(valid))
        return valid

    def write():
        """
        Commits the configuration to file.
        """
        config.write()

def as_bool(string):
    """
    Returns True if the key contains a string that represents True, or is the True object.
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

    if test == 'true' or test == 'yes' or test == 'on' or test == '1':
        return True
    elif test == 'false' or test == 'no' or test == 'off' or test == '0':
        return False
    else:
        raise ValueError('Mangled boolean representation "{0}"'.format(string))

def homeAbsolutePath(filename):
    """
    Evaluates a file's relative path given a cwd of ~/.taxidi/ or %APPDATA%\\.taxidi\\
    :`filename` - Relative or absolute path to a file.
    """
    olddir = os.getcwd()
    os.chdir(os.path.join(homepath, '.taxidi'))
    path = os.path.abspath(filename)
    os.chdir(olddir)  #Switch back to old cwd
    return path

def reload():
    config.reload()

def _main():
    # read out configuration for debugging... and stuff.
    config = Config().config
    print config['report']['email']

if __name__ == "__main__":
    _main()
else:
    config = Config().config
