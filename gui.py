#!/usr/bin/env python
#-*- coding:utf-8 -*-

#TODO: Fix layout issues.  (Held together with duct tape right now.)
#TODO: Theme files.  Colours hard coded for now.
#TODO: Set radiobutton background colours if possible.
#TODO: Clean up XML.

__version__ = '0.70.00-dev'

userHand = 'right'

themeBackgroundColour = '#005889'
themeTextColour = 'white'
themeBanner = 'resources/banner.png'

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

        #Set icon:
        favicon = wx.Icon('resources/taxidi.png', wx.BITMAP_TYPE_PNG, 100, 100)
        self.frame.SetIcon(favicon)

        #Create panels
        self.MainMenu = xrc.XRCCTRL(self.frame, 'MainMenu')
        self.RightHandSearch = xrc.XRCCTRL(self.frame, 'RightHandSearch')
        self.LeftHandSearch = xrc.XRCCTRL(self.frame, 'LeftHandSearch')
        self.RecordPanelRight = xrc.XRCCTRL(self.frame, 'RecordPanelRight')
        self.RecordPanelLeft = xrc.XRCCTRL(self.frame, 'RecordPanelLeft')
        self.VisitorRight = xrc.XRCCTRL(self.frame, 'VisitorRight')

        #Setup panels
        self.setupMainMenu()
        self.setupSearch()

        self.VisitorRight.Hide()


        #self.keypadSizer = self.b1.GetContainingSizer()
        #print self.keypadSizer.thisown
        #self.keypadSizer.Hide(True)

        #Hide all other panels
        self.RightHandSearch.Hide()
        self.LeftHandSearch.Hide()
        self.RecordPanelLeft.Hide()
        self.RecordPanelRight.Hide()

        #Bind events
        self.frame.Bind(wx.EVT_SIZE, self.on_size)

        self.frame.SetBackgroundColour(themeBackgroundColour)

        wximg = wx.Image(themeBanner)
        wxbanner=wximg.ConvertToBitmap()
        self.bitmap = wx.StaticBitmap(self.frame,-1,wxbanner,(0,0))

        self.RightHandSearch.SetPosition((0, 180))
        self.RightHandSearch.SetSize((686, 407))
        self.RightHandSearch.CentreOnParent(dir=wx.HORIZONTAL)
        self.RightHandSearch.Layout()
        self.RightHandSearch.Fit()
        self.RightHandSearch.SetClientSize((self.frame.GetSize()[0]-50, -1))

        self.LeftHandSearch.SetPosition((0, 180))
        self.LeftHandSearch.SetSize((686, 407))
        self.LeftHandSearch.CentreOnParent(dir=wx.HORIZONTAL)
        self.LeftHandSearch.Layout()
        self.LeftHandSearch.Fit()
        self.LeftHandSearch.SetClientSize((self.frame.GetSize()[0]-50, -1))


        #Put everything in a list for convenience when resizing, etc:
        self.panels =      [ self.MainMenu,
                            self.LeftHandSearch,   self.RightHandSearch,
                            self.RecordPanelLeft,  self.RecordPanelRight ]
        self.panelsLeft =  [ self.LeftHandSearch,  self.RecordPanelLeft  ]
        self.panelsRight = [ self.RightHandSearch, self.RecordPanelRight ]

        for i in self.panels:
            i.SetBackgroundColour(themeBackgroundColour)
            i.SetForegroundColour(themeTextColour)

        self.frame.Centre()
        #self.frame.ShowFullScreen(True)
        self.MainMenu.begin.SetFocus()
        self.frame.Show()

    def on_size(self, event):
        """
        Event handler for resizing the window.
        """
        event.Skip()
        size = self.frame.GetSize()
        for i in self.panels:
            i.SetPosition((size[0], 170))
            i.CentreOnParent(dir=wx.HORIZONTAL)
        self.frame.Layout()
        self.bitmap.SetPosition( ( ((size[0]-1020)/2) , 0) ) #Centre the banner

    def setupMainMenu(self):
        #Make it pretty
        self.MainMenu.ClearBackground()
        self.MainMenu.SetBackgroundColour(themeBackgroundColour)
        self.MainMenu.CentreOnParent(dir=wx.HORIZONTAL)
        self.MainMenu.FitInside()

        #Setup button items:
        self.MainMenu.begin = xrc.XRCCTRL(self.MainMenu, 'begin')
        self.MainMenu.configure = xrc.XRCCTRL(self.MainMenu, 'configure')
        self.MainMenu.about = xrc.XRCCTRL(self.MainMenu, 'about')
        self.MainMenu.services = xrc.XRCCTRL(self.MainMenu, 'services')
        self.MainMenu.activities = xrc.XRCCTRL(self.MainMenu, 'activities')
        self.MainMenu.quit = xrc.XRCCTRL(self.MainMenu, 'quit')

        #Bind buttons:
        self.MainMenu.Bind(wx.EVT_BUTTON, self.StartCheckin, self.MainMenu.begin)
        self.MainMenu.Bind(wx.EVT_BUTTON, self.OnAboutBox, self.MainMenu.about)
        self.MainMenu.Bind(wx.EVT_BUTTON, self.Quit, self.MainMenu.quit)

    def setupSearch(self):
        panels = [self.RightHandSearch, self.LeftHandSearch]

        #set text colours:
        for pane in panels:
            pane.st1 = xrc.XRCCTRL(pane, 'st1')
            pane.st2 = xrc.XRCCTRL(pane, 'st2')
            pane.st3 = xrc.XRCCTRL(pane, 'st3')
            pane.st1.SetForegroundColour(themeTextColour)
            pane.st2.SetForegroundColour(themeTextColour)
            pane.st3.SetForegroundColour(themeTextColour)

        #apply colours to buttons:
        for pane in panels:
            pane.UserButton = xrc.XRCCTRL(pane, 'UserButton')
            pane.SearchAny = xrc.XRCCTRL(pane, 'SearchAny')
            pane.SearchName = xrc.XRCCTRL(pane, 'SearchName')
            pane.SearchBarcode = xrc.XRCCTRL(pane, 'SearchBarcode')
            pane.SearchPhone = xrc.XRCCTRL(pane, 'SearchPhone')
            pane.SearchSecure = xrc.XRCCTRL(pane, 'SearchSecure')
            pane.UserButton.SetForegroundColour(themeTextColour)
            pane.SearchAny.SetForegroundColour(themeTextColour)
            pane.SearchName.SetForegroundColour(themeTextColour)
            pane.SearchBarcode.SetForegroundColour(themeTextColour)
            pane.SearchPhone.SetForegroundColour(themeTextColour)
            pane.SearchSecure.SetForegroundColour(themeTextColour)

        #Setup inputs:
        for pane in panels:
            pane.Search = xrc.XRCCTRL(pane, 'Search')
            pane.SearchButton = xrc.XRCCTRL(pane, 'SearchButton')
            pane.ExitButton = xrc.XRCCTRL(pane, 'ExitButton')

            pane.Search.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
            self.frame.Bind(wx.EVT_BUTTON, self.OnSearch, pane.SearchButton)
            self.frame.Bind(wx.EVT_BUTTON, self.ExitSearch, pane.ExitButton)

        #Apply global handles by user configuration.
        if userHand == 'left':
            self.Search = self.LeftHandSearch.Search
        else:
            self.Search = self.RightHandSearch.Search


    def OnSearch(self, event):
        print "OK"

    def HideAll(self):
        """
        Hides all panels defined in self.panels
        """
        for i in self.panels:
            i.Hide()

    def ExitSearch(self, event):
        self.HideAll()
        self.MainMenu.Show()

    def StartCheckin(self, event):
        self.MainMenu.Hide()
        if userHand == 'left':
            self.LeftHandSearch.Show()
        else:
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
        info.SetVersion(__version__)
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
