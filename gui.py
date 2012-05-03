#!/usr/bin/env python
#-*- coding:utf-8 -*-

#TODO: (URGENT DEADLINE 03.05) Create/add multi-service selection panel.
#TODO: (URGENT DEADLINE 03.05) Handle user clicking the splash screen (causes recursion of fork())
#TODO: (HIGH   DEADLINE 03.05) Integrate configuration, theme files.
#TODO: (URGENT DEADLINE 03.05) Add username/password dialogue.

#TODO: Fix layout issues.  (Held together with duct tape right now.)
#TODO: Theme files.  Colours hard coded for now. (Probably something for conf.py)
#TODO: Set radiobutton background colours if possible.
#TODO: Clean up XML.

#Imports for splash screen
import wx
import os
import signal

__version__ = '0.70.01-dev'

userHand = 'right'

#TODO: Read these from a theme file
themeBackgroundColour = '#005889'
themeTextColour = 'white'
themeTextDisabled = '#cecece'
themeToggleColour = '#f07746'
themeCheckOnColour = '#61bd36'
themeCheckOffColour = '#d42b1d'
themeBanner = 'resources/banner.png'

class MyApp(wx.App):

    def OnInit(self):
        self.res = xrc.XmlResource(os.path.join('xrc', 'menu.xrc'))
        self.init_frame()
        os.kill(child_pid, signal.SIGKILL)  #Close the splash
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
        self.VisitorPanelRight = xrc.XRCCTRL(self.frame, 'VisitorRight')
        self.VisitorPanelLeft = xrc.XRCCTRL(self.frame, 'VisitorLeft')
        if conf.as_bool(conf.config['webcam']['enable']):
            self.WebcamPanel = webcam.Panel(self.frame)
            self.setupWebcamPanel()

        #Setup panels
        self.setupMainMenu()
        self.setupSearch()
        self.setupRecordPanel()
        self.setupResultsList()
        self.setupVisitorPanel()

        #self.keypadSizer = self.b1.GetContainingSizer()
        #print self.keypadSizer.thisown
        #self.keypadSizer.Hide(True)

        #Hide all other panels
        #~ self.RightHandSearch.Hide()
        #~ self.LeftHandSearch.Hide()
        #~ self.RecordPanelLeft.Hide()
        #~ self.RecordPanelRight.Hide()


        #Bind events
        self.frame.Bind(wx.EVT_SIZE, self.on_size)

        self.frame.SetBackgroundColour(themeBackgroundColour)

        wximg = wx.Image(themeBanner)
        wxbanner=wximg.ConvertToBitmap()
        self.bitmap = wx.StaticBitmap(self.frame,-1,wxbanner,(0,0))


        #Put everything in a list for convenience when resizing, etc:
        self.panels =      [ self.MainMenu,
                             self.LeftHandSearch,   self.RightHandSearch,
                             self.RecordPanelLeft,  self.RecordPanelRight,
                             self.ResultsPanel,
                             self.VisitorPanelLeft, self.VisitorPanelRight ]
        self.panelsLeft =  [ self.LeftHandSearch,  self.RecordPanelLeft,
                             self.VisitorPanelLeft ]
        self.panelsRight = [ self.RightHandSearch, self.RecordPanelRight,
                             self.VisitorPanelRight ]

        for i in self.panels:
            i.SetBackgroundColour(themeBackgroundColour)
            i.SetForegroundColour(themeTextColour)

        #Hide all other panels:
        self.HideAll()
        self.MainMenu.Show()

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
        for i in self.panels: #Apply position to all panels.
            i.SetPosition((size[0], 160))
            i.CentreOnParent(dir=wx.HORIZONTAL)
        self.frame.Layout()
        self.bitmap.SetPosition( ( ((size[0]-1020)/2) , 0) ) #Centre the banner
        #Custom positions:
        if conf.as_bool(conf.config['webcam']['enable']):
            self.WebcamPanel.CentreOnParent(dir=wx.HORIZONTAL)


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

        #Set initial geometry:
        for pane in panels:
            pane.SetPosition((0, 180))
            pane.SetSize((686, 407))
            pane.CentreOnParent(dir=wx.HORIZONTAL)
            pane.Layout()
            pane.Fit()
            pane.SetClientSize((self.frame.GetSize()[0]-50, -1))

        #Setup inputs:
        for pane in panels:
            pane.Search = xrc.XRCCTRL(pane, 'Search')
            pane.SearchButton = xrc.XRCCTRL(pane, 'SearchButton')
            pane.VisitorButton = xrc.XRCCTRL(pane, 'VisitorButton')
            pane.ExitButton = xrc.XRCCTRL(pane, 'ExitButton')

            pane.Search.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
            self.frame.Bind(wx.EVT_BUTTON, self.OnSearch, pane.SearchButton)
            self.frame.Bind(wx.EVT_BUTTON, self.OnVisitor, pane.VisitorButton)
            self.frame.Bind(wx.EVT_BUTTON, self.ExitSearch, pane.ExitButton)

        #Apply global handles by user configuration.
        if userHand == 'left':
            self.SearchPanel = self.LeftHandSearch
            self.Search = self.LeftHandSearch.Search
        else:
            self.SearchPanel = self.RightHandSearch
            self.Search = self.RightHandSearch.Search

    #TODO: (URGENT DEADLINE 03.05) Add basic record panel UI functionality.
    def setupRecordPanel(self):
        panels = [self.RecordPanelLeft, self.RecordPanelRight]

        #Add static text controls and set font colour:
        for pane in panels:
            #Mutable texts:
            pane.NameText = xrc.XRCCTRL(pane, 'NameText')
            pane.SurnameText = xrc.XRCCTRL(pane, 'SurnameText')
            pane.StatusText = xrc.XRCCTRL(pane, 'StatusText')
            pane.AgeText = xrc.XRCCTRL(pane, 'AgeText')
            pane.CreatedText = xrc.XRCCTRL(pane, 'CreatedText')
            pane.LastSeenText = xrc.XRCCTRL(pane, 'LastSeenText')
            pane.ModifiedText = xrc.XRCCTRL(pane, 'ModifiedText')
            pane.CountText = xrc.XRCCTRL(pane, 'CountText')

            pane.NameText.SetForegroundColour(themeTextColour)
            pane.SurnameText.SetForegroundColour(themeTextColour)
            pane.StatusText.SetForegroundColour(themeTextDisabled)
            pane.AgeText.SetForegroundColour(themeTextColour)
            pane.CreatedText.SetForegroundColour(themeTextColour)
            pane.LastSeenText.SetForegroundColour(themeTextColour)
            pane.ModifiedText.SetForegroundColour(themeTextColour)
            pane.CountText.SetForegroundColour(themeTextColour)

            #Immutable:
            firstSt = xrc.XRCCTRL(pane, 'firstSt')
            lastSt = xrc.XRCCTRL(pane, 'lastSt')
            gradeSt = xrc.XRCCTRL(pane, 'gradeSt')
            phoneSt = xrc.XRCCTRL(pane, 'phoneSt')
            carrierSt = xrc.XRCCTRL(pane, 'carrierSt')
            pagingSt = xrc.XRCCTRL(pane, 'pagingSt')
            dobSt = xrc.XRCCTRL(pane, 'dobSt')
            ageSt = xrc.XRCCTRL(pane, 'ageSt')
            activitySt = xrc.XRCCTRL(pane, 'activitySt')
            roomSt = xrc.XRCCTRL(pane, 'roomSt')
            parent1St = xrc.XRCCTRL(pane, 'parent1St')
            parent2St = xrc.XRCCTRL(pane, 'parent2St')
            emailSt = xrc.XRCCTRL(pane, 'emailSt')
            medicalSt = xrc.XRCCTRL(pane, 'medicalSt')
            notesSt = xrc.XRCCTRL(pane, 'notesSt')
            createdSt = xrc.XRCCTRL(pane, 'createdSt')
            lastSeenSt = xrc.XRCCTRL(pane, 'lastSeenSt')
            modifiedSt = xrc.XRCCTRL(pane, 'modifiedSt')
            countSt = xrc.XRCCTRL(pane, 'countSt')

            firstSt.SetForegroundColour(themeTextColour)
            lastSt.SetForegroundColour(themeTextColour)
            gradeSt.SetForegroundColour(themeTextColour)
            phoneSt.SetForegroundColour(themeTextColour)
            carrierSt.SetForegroundColour(themeTextColour)
            pagingSt.SetForegroundColour(themeTextColour)
            dobSt.SetForegroundColour(themeTextColour)
            ageSt.SetForegroundColour(themeTextColour)
            activitySt.SetForegroundColour(themeTextColour)
            roomSt.SetForegroundColour(themeTextColour)
            parent1St.SetForegroundColour(themeTextColour)
            parent2St.SetForegroundColour(themeTextColour)
            emailSt.SetForegroundColour(themeTextColour)
            medicalSt.SetForegroundColour(themeTextColour)
            notesSt.SetForegroundColour(themeTextColour)
            createdSt.SetForegroundColour(themeTextColour)
            lastSeenSt.SetForegroundColour(themeTextColour)
            modifiedSt.SetForegroundColour(themeTextColour)
            countSt.SetForegroundColour(themeTextColour)

        #Add buttons and their bindings:
        for pane in panels:
            pane.ProfilePicture = xrc.XRCCTRL(pane, 'ProfilePicture')
            pane.CloseButton = xrc.XRCCTRL(pane, 'CloseButton')
            pane.CheckinButton = xrc.XRCCTRL(pane, 'CheckinButton')
            pane.MultiServiceButton = xrc.XRCCTRL(pane, 'MultiServiceButton')
            pane.NametagToggle = xrc.XRCCTRL(pane, 'NametagToggle')
            pane.ParentToggle = xrc.XRCCTRL(pane, 'ParentToggle')
            pane.SaveButton = xrc.XRCCTRL(pane, 'SaveButton')
            pane.BarcodeButton = xrc.XRCCTRL(pane, 'BarcodeButton')
            pane.PhoneButton = xrc.XRCCTRL(pane, 'PhoneButton')
            pane.CustomIDButton = xrc.XRCCTRL(pane, 'CustomIDButton')
            pane.Parent1Find = xrc.XRCCTRL(pane, 'Parent1Find')
            pane.Parent2Find = xrc.XRCCTRL(pane, 'Parent2Find')
            pane.AuthorizePickupButton = xrc.XRCCTRL(pane,
                'AuthorizePickupButton')
            pane.DenyPickupButton = xrc.XRCCTRL(pane, 'DenyPickupButton')
            pane.EmergencyContactButton = xrc.XRCCTRL(pane,
                'EmergencyContactButton')

            self.frame.Bind(wx.EVT_BUTTON, self.CloseRecordPanel, pane.CloseButton)

        #Set initial geometry:
        for pane in panels:
            pane.SetPosition((0, 160))
            pane.SetClientSize((self.frame.GetSize()[0]-20, -1))


    def CloseRecordPanel(self, event):
        self.RecordPanelLeft.Hide()
        self.RecordPanelRight.Hide()
        if self.ResultsPanel.opened:
            self.ShowResultsPanel()
        else:
            self.ShowSearchPanel()


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
        self.ResultsPanel.Bind(wx.EVT_BUTTON, self.DisplaySelectedRecord, self.resultsPanelDisplay)

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

    def DisplaySelectedRecord(self, event):
        self.ShowRecordPanel()
        pass

    def ShowRecordPanel(self):
        self.HideAll()
        if userHand == 'left':
            self.RecordPanelLeft.Show()
        else:
            self.RecordPanelRight.Show()

    def CloseResults(self, event):
        #Clear the list:
        self.ResultsList.DeleteAllItems()
        self.ResultsPanel.opened = False #We use this to know if it's open.
        self.ResultsPanel.Hide()
        self.ShowSearchPanel()

    def setupWebcamPanel(self):
        self.WebcamPanel.live.suspend()
        self.WebcamPanel.SetSize((640, 560))
        self.WebcamPanel.SetPosition((0, 130))
        self.WebcamPanel.CentreOnParent(dir=wx.HORIZONTAL)
        self.WebcamPanel.Hide()

    def setupVisitorPanel(self):
        panels = [self.VisitorPanelRight, self.VisitorPanelLeft]
        #Add static text controls and set font colour:
        for pane in panels:
            #Mutable texts:
            pane.NameText = xrc.XRCCTRL(pane, 'NameText')
            pane.SurnameText = xrc.XRCCTRL(pane, 'SurnameText')
            pane.StatusText = xrc.XRCCTRL(pane, 'StatusText')
            pane.CreatedText = xrc.XRCCTRL(pane, 'CreatedText')
            pane.LastSeenText = xrc.XRCCTRL(pane, 'LastSeenText')
            pane.ModifiedText = xrc.XRCCTRL(pane, 'ModifiedText')
            pane.CountText = xrc.XRCCTRL(pane, 'CountText')

            pane.NameText.SetForegroundColour(themeTextColour)
            pane.SurnameText.SetForegroundColour(themeTextColour)
            pane.StatusText.SetForegroundColour(themeTextDisabled)
            pane.CreatedText.SetForegroundColour(themeTextColour)
            pane.LastSeenText.SetForegroundColour(themeTextColour)
            pane.ModifiedText.SetForegroundColour(themeTextColour)
            pane.CountText.SetForegroundColour(themeTextColour)

            #~ #Immutable:
            firstSt = xrc.XRCCTRL(pane, 'firstSt')
            lastSt = xrc.XRCCTRL(pane, 'lastSt')
            phoneSt = xrc.XRCCTRL(pane, 'phoneSt')
            carrierSt = xrc.XRCCTRL(pane, 'carrierSt')
            pagingSt = xrc.XRCCTRL(pane, 'pagingSt')
            activitySt = xrc.XRCCTRL(pane, 'activitySt')
            roomSt = xrc.XRCCTRL(pane, 'roomSt')
            parent1St = xrc.XRCCTRL(pane, 'parent1St')
            emailSt = xrc.XRCCTRL(pane, 'emailSt')
            medicalSt = xrc.XRCCTRL(pane, 'medicalSt')
            expirySt = xrc.XRCCTRL(pane, 'expirySt')
            createdSt = xrc.XRCCTRL(pane, 'createdSt')
            modifiedSt = xrc.XRCCTRL(pane, 'modifiedSt')
            countSt = xrc.XRCCTRL(pane, 'countSt')
            newsletterToggleSt = xrc.XRCCTRL(pane, 'newsletterToggleSt')
            expiresSt = xrc.XRCCTRL(pane, 'expiresSt')
            neverExpiresSt = xrc.XRCCTRL(pane, 'neverExpireSt')
            notifyWhenExpiresSt = xrc.XRCCTRL(pane, 'notifyWhenExpiresSt')


            firstSt.SetForegroundColour(themeTextColour)
            lastSt.SetForegroundColour(themeTextColour)
            phoneSt.SetForegroundColour(themeTextColour)
            carrierSt.SetForegroundColour(themeTextColour)
            pagingSt.SetForegroundColour(themeTextColour)
            activitySt.SetForegroundColour(themeTextColour)
            roomSt.SetForegroundColour(themeTextColour)
            parent1St.SetForegroundColour(themeTextColour)
            emailSt.SetForegroundColour(themeTextColour)
            medicalSt.SetForegroundColour(themeTextColour)
            expirySt.SetForegroundColour(themeTextColour)
            createdSt.SetForegroundColour(themeTextColour)
            modifiedSt.SetForegroundColour(themeTextColour)
            countSt.SetForegroundColour(themeTextColour)
            newsletterToggleSt.SetForegroundColour(themeTextColour)
            expiresSt.SetForegroundColour(themeTextColour)
            neverExpiresSt.SetForegroundColour(themeTextColour)
            notifyWhenExpiresSt.SetForegroundColour(themeTextColour)

        #~ #Add buttons and their bindings:
        for pane in panels:
            pane.ProfilePicture = xrc.XRCCTRL(pane, 'ProfilePicture')
            pane.CloseButton = xrc.XRCCTRL(pane, 'CloseButton')
            pane.CheckinButton = xrc.XRCCTRL(pane, 'CheckinButton')
            pane.NametagToggle = xrc.XRCCTRL(pane, 'NametagToggle')
            pane.ParentToggle = xrc.XRCCTRL(pane, 'ParentToggle')
            pane.MultiServiceButton = xrc.XRCCTRL(pane, 'MultiServiceButton')
            pane.PhoneButton = xrc.XRCCTRL(pane, 'PhoneButton')
            pane.PhoneButton.Disable()
            pane.CustomIDButton = xrc.XRCCTRL(pane, 'CustomIDButton')
            pane.Parent1Find = xrc.XRCCTRL(pane, 'Parent1Find')
            pane.AddSibling = xrc.XRCCTRL(pane, 'AddSibling')
            pane.NewsletterToggle = xrc.XRCCTRL(pane, 'NewsletterToggle')
            pane.NeverExpireToggle = xrc.XRCCTRL(pane, 'NeverExpireToggle')
            pane.NotifyWhenExpiresToggle = xrc.XRCCTRL(pane, 'NotifyWhenExpiresToggle')

            self.frame.Bind(wx.EVT_BUTTON, self.CloseVisitorPanel, pane.CloseButton)

            pane.ProfilePicture.Bind(wx.EVT_BUTTON, self.VisitorPhoto)

            pane.NametagToggle.SetBackgroundColour(themeToggleColour) #On by default
            pane.NametagToggle.Bind(wx.EVT_TOGGLEBUTTON, self.ToggleState)
            pane.ParentToggle.SetBackgroundColour(themeToggleColour)  #On by default
            pane.ParentToggle.Bind(wx.EVT_TOGGLEBUTTON, self.ToggleState)

            pane.NewsletterToggle.Bind(wx.EVT_TOGGLEBUTTON, self.ToggleCheckBox)
            pane.NeverExpireToggle.Bind(wx.EVT_TOGGLEBUTTON, self.ToggleCheckBox)
            pane.NotifyWhenExpiresToggle.Bind(wx.EVT_TOGGLEBUTTON, self.ToggleCheckBox)

        #Add inputs:
        for pane in panels:
            pane.Phone = xrc.XRCCTRL(pane, 'Phone')
            pane.FirstName = xrc.XRCCTRL(pane, 'FirstName')
            pane.Surname = xrc.XRCCTRL(pane, 'Surname')
            pane.PhoneCarrier = xrc.XRCCTRL(pane, 'PhoneCarrier')
            pane.Paging = xrc.XRCCTRL(pane, 'Paging')
            pane.Activity = xrc.XRCCTRL(pane, 'Activity')
            pane.Room = xrc.XRCCTRL(pane, 'Room')
            pane.Medical = xrc.XRCCTRL(pane, 'Medical')
            pane.Parent1 = xrc.XRCCTRL(pane, 'Parent1')
            pane.Email = xrc.XRCCTRL(pane, 'Email')
            pane.Paging.Disable()

            pane.Phone.Bind(wx.EVT_KILL_FOCUS, self.FormatPhone)
            pane.Phone.Bind(wx.EVT_TEXT, self.FormatPhoneLive)
            pane.Email.Bind(wx.EVT_TEXT, self.FormatEmailLive)

        #Set initial geometry:
        for pane in panels:
            pane.SetPosition((0, 160))
            pane.SetClientSize((self.frame.GetSize()[0]-20, -1))

    def VisitorPhoto(self, evt):
        if conf.as_bool(conf.config['webcam']['enable']): #Webcam enabled?
            #Hide the visitor panel
            self.HideAll()
            #Show the webcam input panel.
            self.ShowWebcamPanel(self.VisitorPhotoCancel)
        else:
            #Just open a file selection dialog.
            path = os.path.abspath(os.path.expanduser(
                conf.config['webcam']['target']))
            self.log.debug("Opened ImageDialog.")
            dlg = ib.ImageDialog(self.frame, path)
            dlg.Centre()
            if dlg.ShowModal() == wx.ID_OK:
                # TODO: Crop picture, save to disc/database
                print "You Selected File: " + dlg.GetFile()
            else:
                self.log.debug("> Dialogue cancelled.")

            dlg.Destroy()
            

    def VisitorPhotoCancel(self, evt):
        self.ShowVisitorPanel()
        self.CloseWebcamPanel()

    def CloseWebcamPanel(self):
        self.WebcamPanel.Unbind(webcam.CONTROLS_CANCEL)
        self.WebcamPanel.live.suspend()
        self.WebcamPanel.Hide()

    def ShowWebcamPanel(self, cancelFunction):
        self.WebcamPanel.Show()
        self.WebcamPanel.Bind(webcam.CONTROLS_CANCEL, cancelFunction)
        self.WebcamPanel.live.resume()
        pass

    def FormatEmailLive(self, event):
        email = event.GetEventObject()
        validate.EmailFormat(email)

    def FormatPhone(self, event):
        phone = event.GetEventObject()
        validate.PhoneFormat(phone)

    def FormatPhoneLive(self, event):
        phone = event.GetEventObject()
        if phone.IsModified():
            validate.PhoneFormat(phone)


    def ToggleState(self, event):
        """
        Changes the background colour of a toggle button to `themeToggleColour` given
        the toggle's state.  Resets to system's default colour when off. Example usage:

            self.panel.MyToggle(wx.EVT_TOGGLEBUTTON, self.ToggleState)

        Useful to make toggle buttons more visible and easier to use.
        """
        btn = event.GetEventObject()
        if btn.GetValue():
            btn.SetBackgroundColour(themeToggleColour) #Toggled on
        else:
            btn.SetBackgroundColour(wx.NullColor) #Toggled off.

    def ToggleCheckBox(self, event):
        """
        Method for making toggle buttons behave more like large checkboxes.
        Sets the appropriate characters and text colour.
        """
        btn = event.GetEventObject()
        if btn.GetValue(): #Toggled on
            btn.SetForegroundColour(themeCheckOnColour)
            btn.SetLabel(u'✔')
        else: #Toggled off
            btn.SetForegroundColour(themeCheckOffColour)
            btn.SetLabel(u'✘')

    def OnVisitor(self, event):
        self.ShowVisitorPanel()

    def ShowVisitorPanel(self):
        self.HideAll()
        if userHand == 'left':
            self.VisitorPanelLeft.Show()
            self.VisitorPanelLeft.FirstName.SetFocus()
        else:
            self.VisitorPanelRight.Show()
            self.VisitorPanelRight.FirstName.SetFocus()

    def CloseVisitorPanel(self, event):
        #TODO: Clear all the inputs
        self.HideAll()
        self.ShowSearchPanel()

    def OnSearch(self, event):
        #Throw up some test data:
        self.ShowResultsPanel()
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

    def ShowResultsPanel(self):
        self.ResultsPanel.opened = True
        self.HideAll()
        self.ResultsPanel.Show()


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
        
#Modified splash screen example from wxPython wiki by Tian Xie.
class SplashScreen(wx.SplashScreen):
    """
    Create a splash screen widget.
    """
    def __init__(self, parent=None):
        # This is a recipe to a the screen.
        # Modify the following variables as necessary.
        aBitmap = wx.Image(name = "resources/splash.png").ConvertToBitmap()
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

def showSplash():
    app = wx.PySimpleApp()
    splash = SplashScreen()
    splash.Show()
    app.MainLoop()
    



if __name__ == '__main__':
    #Fork the process to open the splash screen.
    #TODO:  Make this work in WIN32... maybe.  Pref. make it use threading instead.
    child_pid = os.fork()
    if child_pid == 0:
        #If this is the child process, show splash.
        showSplash()
    else:
        #Parent process: Load the program.
        import os
        import string
        from wx import xrc
        import taxidi
        import conf
        import SearchResultsList
        import validate
        
        if conf.as_bool(conf.config['webcam']['enable']) == True:
            import webcam
        else:
            #Import file selection dialogue instead
            import wx.lib.imagebrowser as ib
        app = MyApp(0)
        app.MainLoop()

            
#~ app = MyApp(0)
#~ app.MainLoop()
