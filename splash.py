#!/usr/bin/env python
#-*- coding: utf-8 -*-

from threading import *
import wx

class SplashScreenThread(Thread):
    """
    Worker thread for forking the splash screen while the program loads.
    """
    def __init__(self):
        Thread.__init__(self)
        #Create splash screen:
        self.app = wx.PySimpleApp()
        self.start()
        
    def run(self):
        self.splash = SplashScreen()
        self.splash.Show()
        self.app.MainLoop()
        return
        
    def abort(self):
        self.splash.Destroy()
        #~ self.app.Exit()
        
#Modified splash screen example from wxPython wiki by Tian Xie.
class SplashScreen(wx.SplashScreen):
    """
    Create a splash screen widget.
    """
    def __init__(self, parent=None):
        # This is a recipe to a the screen.
        # Modify the following variables as necessary.
        aBitmap = wx.Image(name = "/home/redxine/Dropbox/Taxidi/resources/splash.png").ConvertToBitmap()
        splashStyle = wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT
        splashDuration = 10000 # milliseconds
        # Call the constructor with the above arguments in exactly the
        # following order.
        wx.SplashScreen.__init__(self, aBitmap, splashStyle,
                                 splashDuration, parent)
        self.Bind(wx.EVT_CLOSE, self.OnExit)

        wx.Yield()
#----------------------------------------------------------------------#

    def OnExit(self, evt):
        self.Hide()
        self.Close()
        evt.Skip()  # Make sure the default handler runs too...
        
    def Close(self):
        self.Hide()
        self.Destroy()
