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
import taxidi
import SearchResultsList

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

        self.setupResultsList()

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
                            self.RecordPanelLeft,  self.RecordPanelRight,
                            self.ResultsPanel  ]
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
            i.SetPosition((size[0], 160))
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


    def setupResultsList(self):
        u"""
        self.ResultsPanel (panel)
         → self.ResultsControls (panel)
           » controlsSizer (FlexGridSizer)
         → self.ResultsList (SearchResultsList)
        """
        #Create panels
        self.ResultsPanel = wx.Panel(self.frame) #Master panel
        self.ResultsList = SearchResultsList.SearchResultsPanel(self.ResultsPanel) #Display list

        #Perform initial resizes.
        #TODO: Make resizing happen in a sensible way to use all the frame
        self.ResultsList.SetSize((1024, 407))
        self.ResultsPanel.SetSize((1024, 580))
        self.ResultsPanel.SetPosition((0, 160))
        self.ResultsPanel.CentreOnParent(dir=wx.HORIZONTAL)

        self.ResultsControls = wx.Panel(self.ResultsPanel,-1)
        self.ResultsControls.SetBackgroundColour(themeBackgroundColour)

        #Create buttons for the top control panel
        self.resultsPanelPhoto = wx.BitmapButton(self.ResultsControls, -1,
            wx.Bitmap('resources/icons/no-photo-100.png'), size=(100, 100))
        self.resultsPanelClose = wx.BitmapButton(self.ResultsControls, -1,
            wx.Bitmap('resources/icons/window-close.png'), size=(150, 50))
        self.resultsPanelCheckIn = wx.Button(self.ResultsControls, -1,
            'Check-in', size=(150, 50))
        self.resultsPanelCheckIn.SetDefault()
        self.resultsPanelDisplay = wx.Button(self.ResultsControls, -1,
            'Display', size=(150, 50))
        self.resultsPanelMultiService = wx.Button(self.ResultsControls, -1,
            'Multi-Service', size=(150, 50))
        #Group some of the buttons together:
        buttonSizer = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        buttonSizer.Add(self.resultsPanelCheckIn, -1)
        buttonSizer.Add(self.resultsPanelClose, -1)
        buttonSizer.Add(self.resultsPanelMultiService, -1)
        buttonSizer.Add(self.resultsPanelDisplay, -1, wx.RIGHT, border=10)

        #Bind some buttons:
        self.ResultsPanel.Bind(wx.EVT_BUTTON, self.CloseResults, self.resultsPanelClose)

        #Create statictexts:
        self.SearchResultText = wx.StaticText(self.ResultsControls,
            label='Results for 9989')
        self.SearchResultText.SetForegroundColour(themeTextColour)
        font = wx.Font(22, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.SearchResultText.SetFont(font)
        searchInstructions = wx.StaticText(self.ResultsControls,
            label = 'Check one or more records and select an action.\n'
            'To edit or view detals, highlight a record and click "Display".')
        searchInstructions.SetForegroundColour(themeTextColour)
        #And put them in a sizer.
        textBox = wx.FlexGridSizer(rows=2, cols=1, vgap=10, hgap=10)
        textBox.Add(self.SearchResultText, -1)
        textBox.Add(searchInstructions, -1)

        #The master sizer for the whole shebang:
        listSizer = wx.BoxSizer(wx.VERTICAL)
        listSizer.Add(self.ResultsControls, 1, wx.EXPAND)
        listSizer.Add(self.ResultsList, 4, wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)

        #Top-level sizer for ResultsControls panel
        controlsSizer = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        controlsSizer.Add(self.resultsPanelPhoto, -1,
            wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
        controlsSizer.Add(textBox, wx.ALL, border=10)
        #~ controlsSizer.AddSpacer(120)
        controlsSizer.AddStretchSpacer()
        controlsSizer.AddGrowableCol(2)
        controlsSizer.SetFlexibleDirection(wx.HORIZONTAL)
        controlsSizer.Add(buttonSizer, wx.RIGHT | wx.ALIGN_RIGHT, border=30)

        #Add sizers to panels and set layout
        self.ResultsControls.SetAutoLayout(True)
        self.ResultsControls.SetSizer(controlsSizer)
        self.ResultsControls.Layout()

        #Layout the Ultimate List sizer.
        self.ResultsPanel.SetAutoLayout(True)
        self.ResultsPanel.SetSizer(listSizer)
        self.ResultsPanel.Layout()

        #Hide after set-up
        self.ResultsPanel.Hide()

    def CloseResults(self, event):
        #Clear the list:
        self.ResultsList.DeleteAllItems()
        self.ResultsPanel.Hide()
        self.ShowSearchPanel()


    def OnSearch(self, event):
        #Throw up some test data:
        self.HideAll()
        self.ResultsPanel.Show()
        results = [ {'name':'Johnathan Churchgoer', 'activity':'Explorers',  'room':'Jungle Room', 'status':taxidi.STATUS_NONE},
                {'name':'Jane Smith',           'activity':'Explorers',  'room':'Ocean Room',  'status':taxidi.STATUS_CHECKED_IN},
                {'name':'Joseph Flint',         'activity':'Outfitters', 'room':u'—',          'status':taxidi.STATUS_CHECKED_OUT, 'checkout-time':'11:46:34'} ]
        self.ResultsList.ShowResults(results)
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
        self.ShowSearchPanel()

    def ShowSearchPanel(self):
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
