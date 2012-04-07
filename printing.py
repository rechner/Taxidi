#!/usr/bin/env python
#-*- coding:utf-8 -*-

# Handles generation of HTML for nametags, saving/reading printer config, etc.

import os
import platform
import logging
import subprocess
from configobj import ConfigObj

# Platforms using the CUPS printing system (UNIX):
unix = ['Linux', 'linux2', 'Darwin']
wkhtmltopdf = '/usr/bin/wkhtmltopdf' #path to wkhtmltopdf binary
#TODO: Option to select native or builtin wkhtmltopdf

nametags = os.path.join('resources', 'nametag') #path where html can be found.
#For distribution this may be moved to /usr/share/taxidi/ in UNIX.
lpr = '/usr/bin/lpr' #path to LPR program (CUPS/Unix only).

class Printer:
    def __init__(self):
        self.log = logging.getLogger(__name__)
        if platform.system() in unix:
            self.log.info("System is type UNIX. Using CUPS.")
            self.con = _CUPS()
        elif platform.system() == 'win32':
            self.log.info("System is type WIN32. Using GDI.")
            #TODO implement win32 printing code
        else:
            self.log.warning("Unsupported platform. Printing by preview only.")

    def listTemplates(self, directory=nametags):
        """Returns a list of the installed nametag templates"""
        #TODO: add more stringent validation against config and html.
        directory = os.path.abspath(directory)
        self.log.debug("Searching for html templates in {}".format(directory))
        try:
            resource = os.listdir(directory)
        except OSError as e:
            logger.error('({0})'.format(e))
            return []

        themes = []
        #Remove any files from themes that are not directories:
        for i in resource:
            if os.path.isdir(os.path.join(directory, i)):
                themes.append(i)

        valid = []
        #Check that each folder has the corresponding .conf file:
        for i in themes:
            if os.path.isfile(self._getTemplateFile(i)):
                valid.append(i)

        valid.sort()
        del resource, themes
        self.log.debug("Found templates {}".format(valid))
        return valid

    def _getTemplateFile(self, theme, directory=nametags):
        """Returns path to .conf file for a given template pack and check it exists."""
        directory = os.path.abspath(directory)
        path = os.path.join(directory, theme, '{}.conf'.format(theme))
        if os.path.isfile(path):
            return path
        else:
            self.log.warning("{} does not exist or is not file.".format(path))

    def readConfig(self, theme):
        """Reads the configuration for a specified template pack. Returns dictionary."""
        inifile = self._getTemplateFile(theme)
        self.log.info("Reading template configuration from '{0}'".format(inifile))
        config = ConfigObj(inifile)
        try: #check for default section
            default = config['default']
        except KeyError as e:
            self.log.error(e)
            self.log.error("{} contains no [default] section and is invalid.".format(inifile))
            return None
        del default
        return config

    def buildHtmlArguments(self, config, section='default'):
        """Returns list of arguments to pass to wkhtmltopdf. Requires config dictionary
        and section name to read (if None reads [default]).  Works all in lowercase.
        Also returns --allow directory
        """
        piece = config[section]
        args = []
        if len(piece) == 0:
            return []  #No options in section
        for arg in piece.keys():
            if arg.lower() == 'zoom':
                args.append('--zoom')
                args.append(piece[arg])
            elif arg.lower() == 'height':
                args.append('--page-height')
                args.append(piece[arg])
            elif arg.lower() == 'width':
                args.append('--page-width')
                args.append(piece[arg])
            elif arg.lower() == 'left':
                args.append('--margin-left')
                args.append(piece[arg])
            elif arg.lower() == 'right':
                args.append('--margin-right')
                args.append(piece[arg])
            elif arg.lower() == 'top':
                args.append('--margin-top')
                args.append(piece[arg])
            elif arg.lower() == 'bottom':
                args.append('--margin-bottom')
                args.append(piece[arg])
            elif arg.lower() == 'orientation':
                args.append('--orientation')
                args.append(piece[arg].lower())
            else:
                self.log.warning("Unexpected key encountered in {0}: {1} = {2}"
                    .format(section, arg, piece[arg]))
        return args



    #---- printing proxy methods -----

    def listPrinters(self):
        return self.con.listPrinters()

    def getPrinters(self):
        """Returns a list of the names of available system printers (proxy)"""
        return self.con.getPrinters()



class _CUPS():
    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.log.info("Connecting to CUPS server on localhost...")
        import cups
        self.con = cups.Connection()

    def listPrinters(self):
        """Returns a list of the names of available system printers"""
        return self.con.getPrinters().keys()

    def getPrinters(self):
        """Returns dictionary of printer name, description, location, and URI (CUPS)"""
        a = dict()
        printers = self.con.getPrinters()
        for item in printers:
            info = printers[item]['printer-info']
            location = printers[item]['printer-location']
            uri = printers[item]['device-uri']
            a[item] = { 'info' : info, 'location' : location, 'uri' : uri}
        return a




if __name__ == '__main__':
    con = Printer()
    print con.getPrinters()
    print con.listTemplates()

    conf = con.readConfig('default')
    print con.buildHtmlArguments(conf)
