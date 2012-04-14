#!/usr/bin/env python
#-*- coding:utf-8 -*-

# For now the internal nametag templates will be hardcoded.  At least a [default]
# section is required; if a named section is missing the HTML will be ignored,
# otherwise the following sections and files are allowed:
#   - [parent]
#   - [report]
#   - [volunteer]

# TODO: respect locale's date/time format when doing substitution. Hard coded for now.

"""Handles generation of HTML for nametags, saving/reading printer config, etc"""

import os
import re
import platform
import logging
import subprocess
import tempfile
import datetime
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

    def buildArguments(self, config, section='default'):
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
            elif arg.lower() == 'size':
                args.append('-s')
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

    def writePdf(self, args, html, copies=1, collate=True):
        """
        Calls wkhtmltopdf and generates a pdf. Accepts args as a list, path
        to html file, and returns path to temporary file.  Temp file 
        should be unlinked when no longer needed.
        Also accepts copies=1, collate=True
        """
        #Build arguments
        if copies < 0: copies = 1
        if copies != 1:
            args.append("--copies")
            args.append(copies)
        if collate:
            args.append("--collate")
        args.append(html)
            
        #create temp file to write to
        out = tempfile.NamedTemporaryFile(delete=False)
        out.close()
        args.append(out.name) #append output file name
        
        self.log.debug('Calling {0} with arguments <'.format(wkhtmltopdf))
        self.log.debug('{0} >'.format(args))
        
        args.insert(0, wkhtmltopdf) #prepend program name
        
        ret = subprocess.check_call(args)
        if ret != 0:
            self.log.error('Called process error:')
            self.log.error('Program returned exit code {0}'.
                format(ret))
            return 0
        self.log.debug('Generated pdf {0}'.format(out.name))
        return out.name
        
    def preview(self, fileName):
        """Opens a file using the default application. (Print preview)"""
        if os.name == 'posix':
            self.log.debug('Attempting to preview file {0} via xdg-open'
                .format(fileName))
            ret = subprocess.call(('/usr/bin/xdg-open', fileName))
            if ret != 0:
                self.log.error('xdg-open returned non-zero exit code {0}'.format(ret))
                return 1
            return 0
            
        elif os.name == 'mac': #UNTESTED
            self.log.debug('Attempting to preview file {0} via open'
                .format(fileName))
            ret = subprocess.call(['/usr/bin/open', fileName])
            if ret != 0:
                self.log.error('open returned non-zero exit code {0}'.format(ret))
                return 1
            return 0
            
        if os.name == 'nt': #UNTESTED
            self.log.debug('Attempting to preview file {0} via win32.startfile'
                .format(fileName))
            os.startfile(filepath)
            return 0
                               

    #---- printing proxy methods -----

    def listPrinters(self):
        """Returns list of names of available system printers (proxy)."""
        return self.con.listPrinters()

    def getPrinters(self):
        """Returns dictionary of printer name, description, location, and URI (proxy)"""
        return self.con.getPrinters()

class Nametag:
    def __init__(self, barcode=False):
        """
        Format nametags with data using available HTML templates.  Will
        fetch barcode encoding options from global config; otherwise accepts
        barcode=False as the initialization argument.
        """
        #TODO: source config options for barcode encodings, etc. from global config.
        self.barcodeEnable = barcode
        self.log = logging.getLogger(__name__)

    def listTemplates(self, directory=nametags):
        """Returns a list of the installed nametag templates"""
        #TODO: add more stringent validation against config and html.
        directory = os.path.abspath(directory)
        self.log.debug("Searching for html templates in {0}".format(directory))
        try:
            resource = os.listdir(directory)
        except OSError as e:
            logger.error('({0})'.format(e))
            return []

        themes = []
        #Remove any files from themes[] that are not directories:
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
        self.log.debug("Found templates {0}".format(valid))
        return valid

    def _getTemplateFile(self, theme, directory=nametags):
        """Returns full path to .conf file for an installed template pack and check it exists."""
        directory = os.path.abspath(directory)
        path = os.path.join(directory, theme, '{0}.conf'.format(theme))
        #TODO: more stringent checks (is there a matching HTML file?)
        if os.path.isfile(path):
            return path
        else:
            self.log.warning("{0} does not exist or is not file.".format(path))
            
    def _getTemplatePath(self, theme, directory=nametags):
        """Returns absolute path only of template pack"""
        return os.path.join(directory, theme)
        

    def readConfig(self, theme):
        """Reads the configuration for a specified template pack. Returns dictionary."""
        inifile = self._getTemplateFile(theme)
        self.log.info("Reading template configuration from '{0}'".format(inifile))
        config = ConfigObj(inifile)
        try: #check for default section
            default = config['default']
        except KeyError as e:
            self.log.error(e)
            self.log.error("{0} contains no [default] section and is invalid.".format(inifile))
            raise KeyError
        del default
        return config

    def nametag(self, template='default', room='', first='', last='', medical='',
                code='', secure='', barcode=''):
        #TODO: respect system locale's strftime formatting
        #TODO: source local config. and generate barcode if needed.
        """
        Applies data to a nametag template and returns the resulting HTML.
        Accepts template name from listTemplates() as first argument; 'default' if none.
        Accepts the following formats (defaults are blank):
            - room
            - first
            - last
            - medical
            - code
            - secure
            - barcode
            
        This method processes default.html only.
        """
        #Check that theme specified is valid:
        if template != 'default':
            themes = listTemplates()
            if template not in themes:
                self.log.error("Bad template specified.  Using default instead.")
                template = 'default'

        #Read in the HTML from template.
        try:
            directory = self._getTemplatePath(template)
        except KeyError:
            self.log.error("Unable to process template '{0}'. Aborting.".format(template))
            return None
        f = open(os.path.join(directory, 'default.html'))
        inp = f.read()
        f.close()
        
        now = datetime.datetime.now()
        
        #Perform substitutions:
        regex = re.compile(r'%DATE%', re.IGNORECASE)
        inp = regex.sub(now.strftime("%a %d %b, %Y"), inp)
        
        regex = re.compile(r'%TIME%', re.IGNORECASE)
        inp = regex.sub(now.strftime("%H:%M:%S"), inp)
        
        regex = re.compile(r'%ROOM%', re.IGNORECASE)
        inp = regex.sub(room, inp)
        
        regex = re.compile(r'%FIRST%', re.IGNORECASE)
        inp = regex.sub(first, inp)
        
        regex = re.compile(r'%LAST%', re.IGNORECASE)
        inp = regex.sub(last, inp)
        
        regex = re.compile(r'%MEDICAL%', re.IGNORECASE)
        inp = regex.sub(medical, inp)
        
        regex = re.compile(r'%CODE%', re.IGNORECASE)
        inp = regex.sub(code, inp)
        
        regex = re.compile(r'%S%', re.IGNORECASE)
        inp = regex.sub(secure, inp)
        
        if len(medical) > 0:
            regex = re.compile(r"window\.onload\s=\shide\('medical'\)\;", re.IGNORECASE)
            inp = regex.sub('', inp)
            
        
        return inp




class _CUPS:
    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.log.info("Connecting to CUPS server on localhost...")
        try:
            import cups
        except ImportError as e:
            self.log.error("CUPS module not available.  Is CUPS installed? {0}".format(e))
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
    print con.listPrinters()
    print con.getPrinters()

    nametag = Nametag(True)

    templates = nametag.listTemplates()
    print nametag._getTemplateFile(templates[0])

    #pdf = tempfile.NamedTemporaryFile(delete=False)
    #pdf.close()
    conf = nametag.readConfig('default')
    args = con.buildArguments(conf)
    #args.append(pdf.name)
    print args
    print
    #print conf

    #clean up:
    #os.unlink(pdf.name)
    
    #device = Printer()
    #out = device.writePdf(args, 'resources/nametag/default/default.html')
    #device.preview(out)
    #raw_input("Enter to continue")
    #os.unlink(out)

    #html = tempfile.NamedTemporaryFile(suffix='.html', delete=False)
    tmpname = os.path.join(nametag._getTemplatePath('default'), 'temp.html')
    html = open(tmpname, 'w')
    stuff = nametag.nametag(room='Green Room', first='Johnothan', last='Churchgoer',
                          medical='Peanuts', code='O-9999', secure='Z99')
    print stuff
    html.write(stuff)
    html.close()
    device = Printer()
    out = device.writePdf(args, tmpname)
    os.unlink(tmpname)
    
    device.preview(out)
    
    raw_input("Enter to continue")
    os.unlink(out)
