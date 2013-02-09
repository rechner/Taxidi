#!/usr/bin/env python
#-*- coding:utf-8 -*-

from functools import partial
from time import sleep, time
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
        #~ request.setHeader("Access-Control-Allow-Origin", "*")
        request.setHeader("Content-Type", "application/json")
        
        if request.postpath[0] == "print":
            if conf.as_bool(conf.config['printing']['enable']):
                #do printing
                theme = request.args["theme"][0]
                room = request.args["room"][0]
                first = request.args["first"][0]
                last = request.args["last"][0]
                code = request.args["code"][0]
                medical = request.args["medical"][0]
                secure = request.args["secure"][0]
                try: #should be a bool
                    barcode = conf.as_bool(request.args["barcode"][0])
                except ValueError as e:
                    request.setResponseCode(400)
                    return json.dumps({'status' : 'fail',
                                       'reason' : e})
                try: #generate the nametag
                    self.printer.nametag(theme=theme, room=room,
                                         first = first, last=last,
                                         code=code, medical=medical,
                                         secure=secure, barcode=barcode)
                except KeyError as e:
                    request.setResponseCode(500, message=e)
                    return json.dumps({'status' : 'fail',
                                       'reason' : e})
                
                try: #send to the configured printer
                    if conf.config['printing']['printer'] == '' and not debug:
                        self.printer.printout() #Use default printer
                    elif conf.config['printing']['printer'] != '':
                        self.printer.printout(
                            printer=conf.config['printing']['printer'])
                    elif debug:
                        self.printer.preview()
                except printing.PrinterError as e:
                    request.setResponseCode(418, message="I'm a teapot: "
                        .format(e))
                    return json.dumps({'status' : 'fail',
                                       'reason' : e})
                finally:
                    self.printer.cleanup()
                
            else:
                request.setResponseCode(500, message='Printing disabled')
                return json.dumps({'status': 'fail', 
                    'reason' : 'Printing disabled in configuration'})

if __name__ == '__main__':
    serv = PrinterServer()
    site = server.Site(serv)
    reactor.listenTCP(8080, site)
    reactor.run()
