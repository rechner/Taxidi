#!/usr/bin/env python
#-*- coding:utf-8 -*-

STATUS_NONE = 0
STATUS_CHECKED_IN = 1
STATUS_CHECKED_OUT = 2


import os
import random
import urllib
import notify.local as notify

class TaxidiURLOpener(urllib.FancyURLopener):
    version = "Taxidi/0.7"

    def http_error_default(self, url, fp, errcode, errmsg, headers):
        self.taxidi_errcode = errcode
        raise Error(errcode)

urllib._urlopener = TaxidiURLOpener()

#TODO/FIXME: set timeout to much lower.
class SecureCode:
    """
    Generates or fetches uniquely random security codes.
    """
    def __init__(self, url = None):
        """
        Creates new instance of SecureCode class.  If initialized with no arguments,
        code will be generated locally.  Otherwise pass the full URI to code-server.php
        """
        self.url = url
        self.directory = os.path.expanduser(os.path.join('~', '.taxidi', 'codes'))
        if url == None:
            #Generate local codes if needed:
            try:
                f = open(os.path.join(self.directory, 'codes.txt'))
                f.close()
            except IOError:
                #Files don't exist, create them:
                self._create_local()

    def request(self):
        """
        Returns a three digit alpha-numeric secure code.
        """
        if self.url == None:
            #Draw from local:
            return self._request_local()
        else:
            #Try to get them from network
            return self._request_network()

    def _request_network(self):
        opener = urllib.FancyURLopener()
        try:
            f = opener.open(self.url)
        except Error as e:
            #Get from local instead
            response = self._request_local()
            notify.warning("Warning", "Unable to poll secure code server. " \
                "Security code was generated locally.")
        else:
            response = f.read().strip('\n')
            if len(response) > 4: #Response is too long to be code
                response = self._request_local()
                notify.warning("Warning", "Unable to poll secure code server. " \
                "Security code was generated locally.")
        finally:
            f.close()
        return response

    def _request_local(self):
        """
        Draw from the local secure codes.
        """
        #Read the index:
        f = open(os.path.join(self.directory, 'codes.index'))
        index = int(f.readline())
        f.close()

        #Read the i'th line
        f = open(os.path.join(self.directory, 'codes.txt'))
        codes = f.read().split('\n')
        f.close()

        #Incrament the index
        f = open(os.path.join(self.directory, 'codes.index'), 'w')
        f.write(str(index + 1))
        f.close()

        return codes[index]


    def _create_local(self):
        alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        numbers = range(0, 10)

        try:
            os.makedirs(self.directory)
        except os.error:
            pass #ignore already created directory

        #Write out the permutations
        fh = open(os.path.join(self.directory, 'codes.txt'), 'w')
        for i in alpha:
            for j in numbers:
                for k in alpha:
                    fh.write('{0}{1}{2}\n'.format(i, j, k))

        for i in numbers:
            for j in alpha:
                for k in numbers:
                    fh.write('{0}{1}{2}\n'.format(i, j, k))

        for i in alpha:
            for j in alpha:
                for k in numbers:
                    fh.write('{0}{1}{2}\n'.format(i, j, k))
        fh.close()

        #Shuffle the file
        import random
        f = open(os.path.join(self.directory, 'codes.txt'))
        contents = f.read()
        f.close()

        aslist = contents.split("\n")
        shuffled = random.sample(xrange(len(aslist)), len(aslist))
        o = open(os.path.join(self.directory, 'codes.txt'), 'w')
        for i in shuffled:
            o.write(aslist[i] + "\n")
        o.close()

        #Initialize the index:
        ind = open(os.path.join(self.directory, 'codes.index'), 'w')
        ind.write('0')
        ind.close()

        return 0

class Error(Exception):
    def __init__(self, code, value=''):
        self.error = value
        self.code = code
    def __str__(self):
        return repr(self.error)


if __name__ == '__main__':
    #Try getting a secure code from server:
    #~ security = SecureCode("http://doesnotresolve.com/script.php")
    security = SecureCode()
    print security.request()
