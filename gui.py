#!/usr/bin/env python
#-*- coding:utf-8 -*-

#TODO: Fix layout issues.  (Held together with duct tape right now.)
#TODO: Theme files.  Colours hard coded for now.
#TODO: Set radiobutton background colours if possible.
#TODO: Clean up XML.

import os
import wx
from wx import xrc

class MyApp(wx.App):

    def OnInit(self):
        self.res = xrc.XmlResource(os.path.join('xrc', 'menu.xrc'))
        self.init_frame()
        return True

    def init_frame(self):
        #Load resources
        self.frame = self.res.LoadFrame(None, 'MyFrame')

        #Panels
        self.RightHandSearch = xrc.XRCCTRL(self.frame, 'RightHandSearch')
        self.LeftHandSearch = xrc.XRCCTRL(self.frame, 'LeftHandSearch')
        self.MainMenu = xrc.XRCCTRL(self.frame, 'MainMenu')

        self.begin = xrc.XRCCTRL(self.MainMenu, 'begin')
        self.configure = xrc.XRCCTRL(self.MainMenu, 'configure')
        self.about = xrc.XRCCTRL(self.MainMenu, 'about')
        self.quit = xrc.XRCCTRL(self.MainMenu, 'quit')

        #set text colours:
        st1 = xrc.XRCCTRL(self.RightHandSearch, 'st1')
        st2 = xrc.XRCCTRL(self.RightHandSearch, 'st2')
        st3 = xrc.XRCCTRL(self.RightHandSearch, 'st3')
        st1.SetForegroundColour("white")
        st2.SetForegroundColour("white")
        st3.SetForegroundColour("white")
        self.UserButton = xrc.XRCCTRL(self.RightHandSearch, 'UserButton')
        self.SearchAny = xrc.XRCCTRL(self.RightHandSearch, 'SearchAny')
        self.SearchName = xrc.XRCCTRL(self.RightHandSearch, 'SearchName')
        self.SearchBarcode = xrc.XRCCTRL(self.RightHandSearch, 'SearchBarcode')
        self.SearchPhone = xrc.XRCCTRL(self.RightHandSearch, 'SearchPhone')
        self.SearchSecure = xrc.XRCCTRL(self.RightHandSearch, 'SearchSecure')
        self.UserButton.SetForegroundColour("white")
        self.UserButton.SetBackgroundColour("#00588999") #FIXME: This has no effect
        self.SearchAny.SetForegroundColour("white")
        self.SearchName.SetForegroundColour("white")
        self.SearchBarcode.SetForegroundColour("white")
        self.SearchPhone.SetForegroundColour("white")
        self.SearchSecure.SetForegroundColour("white")

        #Setup input:
        self.Search = xrc.XRCCTRL(self.RightHandSearch, 'Search')
        self.SearchButton = xrc.XRCCTRL(self.RightHandSearch, 'SearchButton')
        self.ExitButton = xrc.XRCCTRL(self.RightHandSearch, 'ExitButton')
        #self.frame.Bind(wx.EVT_TEXT_ENTER, self.OnSearch, self.Search)
        self.frame.Bind(wx.EVT_TEXT_ENTER, self.OnSearch, self.Search)
        self.frame.Bind(wx.EVT_BUTTON, self.ExitSearch, self.ExitButton)

        #self.keypadSizer = self.b1.GetContainingSizer()
        #print self.keypadSizer.thisown
        #self.keypadSizer.Hide(True)

        #Hide all other panels
        self.RightHandSearch.Hide()
        self.LeftHandSearch.Hide()

        #Bind events
        self.frame.Bind(wx.EVT_SIZE, self.on_size)
        self.frame.Bind(wx.EVT_BUTTON, self.StartCheckin, self.begin)
        self.frame.Bind(wx.EVT_BUTTON, self.OnAboutBox, self.about)
        self.frame.Bind(wx.EVT_BUTTON, self.Quit, self.quit)

        self.MainMenu.ClearBackground()
        self.MainMenu.SetBackgroundColour("#005889")
        self.RightHandSearch.SetBackgroundColour("#005889")
        self.frame.SetBackgroundColour("#005889")
        self.frame.SetBackgroundColour("#005889")

        wximg = wx.Image('resources/banner.png')
        wxbanner=wximg.ConvertToBitmap()
        self.bitmap = wx.StaticBitmap(self.frame,-1,wxbanner,(0,0))

        self.MainMenu.SetPosition((0, 180))
        self.MainMenu.CentreOnParent(dir=wx.HORIZONTAL)
        self.MainMenu.FitInside()

        self.RightHandSearch.SetPosition((0, 180))
        self.RightHandSearch.SetSize((686, 407))
        self.RightHandSearch.CentreOnParent(dir=wx.HORIZONTAL)
        self.RightHandSearch.Layout()
        self.RightHandSearch.Fit()
        self.RightHandSearch.SetClientSize((self.frame.GetSize()[0]-50, -1))

        self.frame.Centre()
        #self.frame.ShowFullScreen(True)
        self.begin.SetFocus()
        self.frame.Show()

    def on_size(self, event):
        event.Skip()
        size = self.frame.GetSize()
        position = self.MainMenu.GetPosition()
        self.MainMenu.SetPosition((size[0], 180))
        self.MainMenu.CentreOnParent(dir=wx.HORIZONTAL)
        self.RightHandSearch.CentreOnParent(dir=wx.HORIZONTAL)
        #self.RightHandSearch.SetClientSize((size[0]-50, -1))

        self.frame.Layout()
        self.bitmap.SetPosition( ( ((size[0]-1020)/2) , 0) )

    def OnSearch(self, event):
        print "OK"

    def ExitSearch(self, event):
        self.RightHandSearch.Hide()
        self.MainMenu.Show()

    def StartCheckin(self, event):
        self.MainMenu.Hide()
        self.RightHandSearch.Show()
        self.Search.SetFocus()


    def OnAboutBox(self, event):
        description = """Taxídí is a free and open source check-in system for nurseries,
churches, and classes. It can be used to track attendance
or at events where attendance must be tracked.

Taxidi was originally written by Zac Sturgeon
and Britt McGlamry for
Journey Church in Millbrook, Alabama.
This version was designed, written, and made
free software by Zac Sturgeon.
"""

        licence = "/Taxidi/ is available under the terms of the GNU GPL v3 or later.\n\n"
        #load LICENSE text:
        f = open('LICENSE')
        licence += f.read()
        f.close()

        info = wx.AboutDialogInfo()

        info.SetIcon(wx.Icon(os.path.join('resources', 'taxidi.png'), wx.BITMAP_TYPE_PNG))
        info.SetName('Taxídí')
        info.SetVersion('0.02-preview')
        info.SetDescription(description)
        info.SetCopyright('© 2012 JKL Tech, Inc')
        info.SetWebSite(('http://jkltech.net/taxidi', 'Project Website'))
        info.SetLicence(licence)
        info.AddDeveloper('Zac Sturgeon')
        info.AddDocWriter('Britt McGlamry')
        info.AddArtist('Zac Sturgeon')
        info.AddArtist('Heather McGlamry')

        #info.AddTranslator('')
        wx.AboutBox(info)

    def Quit(self, event):
        self.frame.Close()
        app.ExitMainLoop()



app = MyApp(0)
app.MainLoop()
