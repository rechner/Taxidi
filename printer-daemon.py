#!/usr/bin/env python
#-*- coding:utf-8 -*-

#TODO: Add parent, volunteer nametag printing
#TODO: Implement printing between multiple hosts (PHP side?, avahi?)
#TODO: Catch first-run config install

from functools import partial
from time import sleep
from twisted.web import server, resource
from twisted.internet import reactor, defer
from twisted.application import internet, service
import json

import conf
import printing

debug = True

class PrinterServer(resource.Resource):
    isLeaf = True
    
    def __init__(self):
        self.printer = printing.Main()

    def render_GET(self, request):
        if conf.as_bool(conf.config['printing']['enable']) == False:
            request.setResponseCode(500, message='Printing disabled')
            return json.dumps({'status': 'fail', 
                    'reason' : 'Printing disabled in configuration'})

        if request.postpath[0] == "nametag":
            request.setHeader("Content-Type", "application/json")
            
            #do printing
            try:
                theme = request.args["theme"][0]
                room = request.args["room"][0]
                first = request.args["first"][0]
                last = request.args["last"][0]
                code = request.args["code"][0]
                medical = request.args["medical"][0]
                secure = request.args["secure"][0]
            except KeyError as e:
                request.setResponseCode(400, message=e)
                return json.dumps({'status' : 'fail',
                       'reason' : 'Missing argument: '+str(e)})
                
            try: #should be a bool
                barcode = conf.as_bool(request.args["barcode"][0])
            except (ValueError, KeyError) as e:
                request.setResponseCode(400)
                return json.dumps({'status' : 'fail',
                                   'reason' : str(e)})
            try: #generate the nametag
                if theme == None: theme = 'default'
                self.printer.nametag(theme=theme, room=room,
                                     first=first, last=last,
                                     code=code, medical=medical,
                                     secure=secure, barcode=barcode)
            except KeyError as e:
                request.setResponseCode(500, message=e)
                return json.dumps({'status' : 'fail',
                       'reason' : 'Nametag generator: '+str(e)})
            
            try: #send to the configured printer
                if conf.config['printing']['printer'] == '' and not debug:
                    self.printer.printout() #Use default printer
                elif conf.config['printing']['printer'] != '':
                    self.printer.printout(
                        printer=conf.config['printing']['printer'])
                elif debug:
                    self.printer.preview()
                    sleep(2)
            except printing.PrinterError as e:
                request.setResponseCode(418, message="I'm a teapot: "
                    .format(e))
                return json.dumps({'status' : 'fail',
                                   'reason' : str(e)})
            finally:
                request.setResponseCode(202, 
                    message="Queued for printing")
                self.printer.cleanup()
                return json.dumps({'status' : 'okay'})

                    
        elif request.postpath[0] == "parent":
            request.setHeader("Content-Type", "application/json")
            #print parent tag
            try:
                theme = request.args["theme"][0]
                room = request.args["room"][0]
                first = request.args["first"][0]
                last = request.args["last"][0]
                code = request.args["code"][0]
                secure = request.args["secure"][0]
                link = request.args["link"][0] #None is valid here
            except KeyError as e:
                request.setResponseCode(400, message=e)
                return json.dumps({'status' : 'fail',
                       'reason' : 'Missing argument: '+str(e)})
            try: #should be a bool
                barcode = conf.as_bool(request.args["barcode"][0])
            except (ValueError, KeyError) as e:
                request.setResponseCode(400)
                return json.dumps({'status' : 'fail',
                                   'reason' : str(e)})
            
            try:
                self.printer.parent(theme=theme, room=room,
                                    first=first, last=last,
                                    code=code, secure=secure,
                                    link=link, barcode=barcode)
            except KeyError as e:
                request.setResponseCode(500, message=e)
                return json.dumps({'status' : 'fail',
                       'reason' : 'Nametag generator: '+str(e)})
            
            try: #send to the configured printer
                if conf.config['printing']['printer'] == '' and not debug:
                    self.printer.printout() #Use default printer
                elif conf.config['printing']['printer'] != '':
                    self.printer.printout(
                        printer=conf.config['printing']['printer'])
                elif debug:
                    self.printer.preview()
                    sleep(2)
            except printing.PrinterError as e:
                request.setResponseCode(418, message="I'm a teapot: "
                    .format(e))
                return json.dumps({'status' : 'fail',
                                   'reason' : str(e)})
            finally:
                request.setResponseCode(202, 
                    message="Queued for printing")
                self.printer.cleanup()
                return json.dumps({'status' : 'okay'})
                
        elif request.postpath[0] == "volunteer":
            request.setHeader("Content-Type", "application/json")
            #print volunteer nametag
            try:
                theme = request.args["theme"][0]
                room = request.args["room"][0]
                first = request.args["first"][0]
                last = request.args["last"][0]
                ministry = request.args["ministry"][0]
            except KeyError as e:
                request.setResponseCode(400, message=e)
                return json.dumps({'status' : 'fail',
                       'reason' : 'Missing argument: '+str(e)})
            
            try: #generate nametag
                self.printer.volunteer(theme=theme, room=room,
                                       first=first, last=last,
                                       ministry=ministry)
            except KeyError as e:
                request.setResponseCode(500, message=e)
                return json.dumps({'status' : 'fail',
                       'reason' : 'Nametag generator: '+str(e)})
                       
            try: #send to the configured printer
                if conf.config['printing']['printer'] == '' and not debug:
                    self.printer.printout() #Use default printer
                elif conf.config['printing']['printer'] != '':
                    self.printer.printout(
                        printer=conf.config['printing']['printer'])
                elif debug:
                    self.printer.preview()
                    sleep(2)
            except printing.PrinterError as e:
                request.setResponseCode(418, message="I'm a teapot: "
                    .format(e))
                return json.dumps({'status' : 'fail',
                                   'reason' : str(e)})
            finally:
                request.setResponseCode(202, 
                    message="Queued for printing")
                self.printer.cleanup()
                return json.dumps({'status' : 'okay'})
            
                
        else:
            request.setResponseCode(418, message="I'm a teapot: ")
            request.setHeader("Content-Type", "text/html")
            return """<html><h1>HTTP Error 418: I'm a teapot.</h1><p>
                Entity may also be short and stout</p><hr>
                <i><a href="http://jkltech.net/taxidi/">Taxidi</a>
                 print server on {0}</i></html>""".format(request.prePathURL())

if __name__ == '__main__':
    serv = PrinterServer()
    site = server.Site(serv)
    reactor.listenTCP(8080, site)
    reactor.run()
