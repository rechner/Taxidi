#!/usr/bin/env python
#-*- coding:utf-8 -*-

#TODO: (URGENT DEADLINE 03.05) Create/add multi-service selection panel.
#TODO: (HIGH   DEADLINE 03.05) Integrate configuration, theme files.
#TODO: (URGENT DEADLINE 03.05) Add username/password dialogue.

#TODO: Fix layout issues.  (Held together with duct tape right now.)
#TODO: Theme files.  Colours hard coded for now. (Probably something for conf.py)
#TODO: Set radiobutton background colours if possible.
#TODO: Clean up XML.

#Couldn't get the wx-esque validator classes to work, so I wrote my own (validate.py)

#Imports for splash screen
import wx
import os
import signal

__version__ = '0.70.02-dev'

userHand = 'right'

#TODO: Read these from a theme file
themeBackgroundColour = '#005889'
themeTextColour = 'white'
themeTextDisabled = '#cecece'
themeToggleColour = '#f07746'
themeCheckOnColour = '#61bd36'
themeCheckOffColour = '#d42b1d'
themeBanner = 'resources/banner.png'
themeIconPath = os.path.abspath('resources/icons/')

class MyApp(wx.App):

    def OnInit(self):
        self.log = logging.getLogger(__name__)  #Setup logging
        self.res = xrc.XmlResource(os.path.join('xrc', 'menu.xrc'))
        self.init_frame()
        self.PhotoStorage = webcam.Storage()

        os.kill(child_pid, signal.SIGKILL)  #Close the splash
        #Setup error handling:
        #~ import sys
        #~ sys.excepthook = self._excepthook
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

        #Setup programme menus:
        self.InitMenus()

        #Load generic icons
        self.NoPhoto128 = wx.Image(os.path.join(themeIconPath, 'no-photo-128.png')).ConvertToBitmap()

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


    def setupDatabase(self):
        #Read user config and import the appropriate database.
        if conf.config['database']['driver'].lower() == 'sqlite':
            datafile = conf.homeAbsolutePath(conf.config['database']['file'])
            import dblib.sqlite as database
            self.database = database
            try:
                self.db = database.Database(datafile)
            except TypeError:
                wx.MessageBox('Unable to open {0}. The file may be write protected.'. \
                    format(datafile), 'Database Error', wx.OK | wx.ICON_ERROR)
            except database.sqlite.OperationalError:
                wx.MessageBox('Unable to open database file:\n{0}'. \
                    format(datafile), 'Database Error', wx.OK | wx.ICON_ERROR)
                return 1
            if self.db.status == database.NEW:
                #The database was newly created
                wx.MessageBox('A new database was created at\n{0}\n Please '
                    'confirm your configuration before continuing.'.format(datafile),
                    'Taxidi', wx.OK | wx.ICON_INFORMATION)

    def InitMenus(self):
        #Setup the programme menus
        self.frame.Bind(wx.EVT_MENU, self.OnAboutBox, id=xrc.XRCID("MenuAbout"))

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
        #~ self.MainMenu.Bind(wx.EVT_BUTTON, self.ShowConfiguration, self.MainMenu.configure)
        self.MainMenu.Bind(wx.EVT_BUTTON, self.EditServices, self.MainMenu.services)
        #~ self.MainMenu.Bind(wx.EVT_BUTTON, self.EditActivities, self.MainMenu.activities)
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

        #Radiobutton bindings:
        for pane in panels:
            pane.SearchAny.Bind(wx.EVT_RADIOBUTTON, self.searchRadioButtonClick)
            pane.SearchName.Bind(wx.EVT_RADIOBUTTON, self.searchRadioButtonClick)
            pane.SearchBarcode.Bind(wx.EVT_RADIOBUTTON, self.searchRadioButtonClick)
            pane.SearchPhone.Bind(wx.EVT_RADIOBUTTON, self.searchRadioButtonClick)
            pane.SearchSecure.Bind(wx.EVT_RADIOBUTTON, self.searchRadioButtonClick)

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
            pane.ClearButton = xrc.XRCCTRL(pane, 'ClearButton')
            pane.SearchButton = xrc.XRCCTRL(pane, 'SearchButton')
            pane.VisitorButton = xrc.XRCCTRL(pane, 'VisitorButton')
            pane.SwitchUserButton = xrc.XRCCTRL(pane, 'SwitchUserButton')
            pane.ExitButton = xrc.XRCCTRL(pane, 'ExitButton')

            pane.Search.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
            pane.Search.Bind(wx.EVT_TEXT, self.ResetSearchColour)
            pane.ClearButton.Bind(wx.EVT_BUTTON, self.clearSearchEvent)
            self.frame.Bind(wx.EVT_BUTTON, self.OnSearch, pane.SearchButton)
            self.frame.Bind(wx.EVT_BUTTON, self.OnVisitor, pane.VisitorButton)
            self.Bind(wx.EVT_BUTTON, self.SwitchUser, pane.SwitchUserButton)
            self.frame.Bind(wx.EVT_BUTTON, self.ExitSearch, pane.ExitButton)

        #Setup keypad:
        for pane in panels:
            pane.b0 = xrc.XRCCTRL(pane, 'b0')
            pane.b1 = xrc.XRCCTRL(pane, 'b1')
            pane.b2 = xrc.XRCCTRL(pane, 'b2')
            pane.b3 = xrc.XRCCTRL(pane, 'b3')
            pane.b4 = xrc.XRCCTRL(pane, 'b4')
            pane.b5 = xrc.XRCCTRL(pane, 'b5')
            pane.b6 = xrc.XRCCTRL(pane, 'b6')
            pane.b7 = xrc.XRCCTRL(pane, 'b7')
            pane.b8 = xrc.XRCCTRL(pane, 'b8')
            pane.b9 = xrc.XRCCTRL(pane, 'b9')
            pane.clear = xrc.XRCCTRL(pane, 'clear')
            pane.accept = xrc.XRCCTRL(pane, 'accept')

            pane.b0.Bind(wx.EVT_BUTTON, self.searchKeypadEvent)
            pane.b1.Bind(wx.EVT_BUTTON, self.searchKeypadEvent)
            pane.b2.Bind(wx.EVT_BUTTON, self.searchKeypadEvent)
            pane.b3.Bind(wx.EVT_BUTTON, self.searchKeypadEvent)
            pane.b4.Bind(wx.EVT_BUTTON, self.searchKeypadEvent)
            pane.b5.Bind(wx.EVT_BUTTON, self.searchKeypadEvent)
            pane.b6.Bind(wx.EVT_BUTTON, self.searchKeypadEvent)
            pane.b7.Bind(wx.EVT_BUTTON, self.searchKeypadEvent)
            pane.b8.Bind(wx.EVT_BUTTON, self.searchKeypadEvent)
            pane.b9.Bind(wx.EVT_BUTTON, self.searchKeypadEvent)
            pane.clear.Bind(wx.EVT_BUTTON, self.clearSearchEvent)
            pane.accept.Bind(wx.EVT_BUTTON, self.OnSearch)

    def searchKeypadEvent(self, event):
        button = event.GetEventObject()
        self.Search.AppendText(button.GetLabel())
        self.Search.SetFocus()
        self.Search.SetInsertionPointEnd()

    def clearSearchEvent(self, event):
        self.Search.Clear()
        self.Search.SetFocus()

    def searchRadioButtonClick(self, event):
        self.Search.SetFocus()


    def EditServices(self, event):
        self.setupDatabase() #Open database
        if self.PerformAuthentication(admin=conf.config['authentication']['config']):
            #Access granted
            dlg = dialogues.EditServices(self.frame, -1, self.db)  #Open dialogue
            dlg.SetServices(self.db.GetServices()) #Set dialogue data (FIXME: do in EditServices class)
            dlg.ShowModal() #Show dialogue
            self.db.commit() #Just in case.
        self.db.close() #close connection when done.


    def PerformAuthentication(self, main=False, admin=False):
        """
        Returns True if the user answered the authentication prompt successfully.
        Also sets the self.user variable with the appropriate data.
        Returns False if user cancelled prompt. (Loops until user cancels).
        """
        conf.config.reload()
        #No password needed
        if conf.config['authentication']['method'].lower() == 'none' \
          or conf.as_bool(conf.config['authentication']['startup']) == False:
            #Access granted
            self.user = {'user': 'admin', 'admin': True, 'leftHanded': False }
            if main: self.SwitchUserDisable() #No other users to switch to
            return True
        #Single user mode:
        elif conf.config['authentication']['method'].lower() == 'single' \
          and conf.as_bool(conf.config['authentication']['startup']):
            #~ print "Hash: ", conf.config['authentication']['hash']
            hashobj = hashlib.sha256()
            response = ''
            while response != None:
                response = dialogues.askPass()
                if response == '': response = None
                if response != None: hashobj.update(response)
                #~ print "Computed hash: ", hashobj.hexdigest()
                if response == None: break
                elif conf.config['authentication']['hash'] == hashobj.hexdigest():
                    #Access granted
                    #Set local user to admin (defaults)
                    self.user = {'user': 'admin', 'admin': True, 'leftHanded': False }
                    if main: self.SwitchUserDisable() #No other users to switch to
                    return True
                    response = None #Just in case
                elif conf.config['authentication']['hash'] != hashobj.hexdigest():
                    #TODO: Nicer message boxes
                    wx.MessageBox('Incorrect Password.', 'Taxidi', wx.OK | wx.ICON_EXCLAMATION)
        #Authenticate user:
        elif conf.config['authentication']['method'].lower() == 'database' \
          and conf.as_bool(conf.config['authentication']['startup']):
            response = ''
            while response != None:
                response = dialogues.askLogin()
                #~ if response == ('', ''): response = None
                if response == None: break
                if self.db.AuthenticateUser(*response):
                    #Access granted, but check if admin is required first:
                    user = self.db.GetUser(response[0])
                    if admin:
                        if user['admin']:
                            #Admin required, and user has admin priveledge: Grant access
                            self.user = user
                            return True
                        else:
                            #Admin required, but user isn't an administrator:
                            wx.MessageBox('You do not have sufficient '
                            'privileges to access this area.  Please contact '
                            'your systems administrator for making changes.',
                            'Taxidi', wx.OK | wx.ICON_ERROR)
                            return False
                    else:
                        #Admin not required
                        self.user = user
                        return True
                    response = None
                else:
                    #Access denied
                    wx.MessageBox('Incorrect username or password.', 'Taxidi',
                        wx.OK | wx.ICON_EXCLAMATION)
        else:
            wx.MessageBox(
              '"{0}" is not a valid authentication method.\n' \
              'Please check your program configuration.'.
              format(conf.config['authentication']['method']),
              'Configuration Error', wx.OK | wx.ICON_ERROR)

        return False

    #TODO: (URGENT DEADLINE 04.05) Add basic record panel UI functionality.
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

        #Setup inputs:
        for pane in panels:
            pane.DOB = xrc.XRCCTRL(pane, 'DOB')
            #~ validator = ObjectAttrValidator2.ObjectAttrTextValidator( pane, 'DOB',
                #~ DateFormatter(), False, self._validationCB )
            #~ pane.DOB.Validator = validator
            pane.DOB.Bind(wx.EVT_TEXT, self.FormatDateLive)
            pane.DOB.Bind(wx.EVT_SET_FOCUS, self.FormatDate)
            pane.DOB.Bind(wx.EVT_KILL_FOCUS, self.FormatDatePost)

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

            pane.CloseButton.Bind(wx.EVT_BUTTON, self.CloseRecordPanel)

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

        #A few variables:
        self.ResultsPanel.opened = None

    def DisplaySelectedRecord(self, event):
        self.ShowRecordPanel()
        pass

    def ShowRecordPanel(self):
        self.HideAll()
        if self.user['leftHanded']:
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
            pane.ExpiryText = xrc.XRCCTRL(pane, 'ExpiryText')
            pane.ModifiedText = xrc.XRCCTRL(pane, 'ModifiedText')
            pane.CountText = xrc.XRCCTRL(pane, 'CountText')

            pane.NameText.SetForegroundColour(themeTextColour)
            pane.SurnameText.SetForegroundColour(themeTextColour)
            pane.StatusText.SetForegroundColour(themeTextDisabled)
            pane.CreatedText.SetForegroundColour(themeTextColour)
            pane.ExpiryText.SetForegroundColour(themeTextColour)
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
            pane.PhoneButton.Disable() #TODO: Phone button actions?
            pane.CustomIDButton = xrc.XRCCTRL(pane, 'CustomIDButton') #TODO Custom ID Button (paging code)
            pane.Parent1Find = xrc.XRCCTRL(pane, 'Parent1Find')
            pane.AddSibling = xrc.XRCCTRL(pane, 'AddSibling')
            pane.NewsletterToggle = xrc.XRCCTRL(pane, 'NewsletterToggle')
            pane.NeverExpireToggle = xrc.XRCCTRL(pane, 'NeverExpireToggle')
            pane.NotifyWhenExpiresToggle = xrc.XRCCTRL(pane, 'NotifyWhenExpiresToggle')

            pane.CheckinButton.Bind(wx.EVT_BUTTON, self.RegisterVisitor)
            pane.CloseButton.Bind(wx.EVT_BUTTON, self.CloseVisitorPanel)
            pane.Parent1Find.Bind(wx.EVT_BUTTON, self.VisitorParentFind)
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
            pane.DatePicker = xrc.XRCCTRL(pane, 'DatePicker')
            pane.Paging.Disable()

            pane.DatePicker.Bind(wx.EVT_DATE_CHANGED, self.VisitorDateChanged)
            pane.Phone.Bind(wx.EVT_KILL_FOCUS, self.FormatPhone)
            pane.Phone.Bind(wx.EVT_TEXT, self.FormatPhoneLive)
            pane.FirstName.Bind(wx.EVT_TEXT, self.ResetBackgroundColour)
            pane.Surname.Bind(wx.EVT_TEXT, self.ResetBackgroundColour)
            pane.Activity.Bind(wx.EVT_CHOICE, self.OnSelectActivity)
            pane.Email.Bind(wx.EVT_TEXT, self.FormatEmailLive)
            pane.Parent1.Bind(wx.EVT_TEXT_ENTER, self.VisitorParentFind)
            pane.Parent1Find.Bind(wx.EVT_NAVIGATION_KEY, self.VisitorParentTab)
            pane.Email.Bind(wx.EVT_NAVIGATION_KEY, self.VisitorParentTab)

            #~ pane.Activity.SetItems()

        #Set initial geometry:
        for pane in panels:
            pane.SetPosition((0, 160))
            pane.SetClientSize((self.frame.GetSize()[0]-20, -1))

        #Initialize stored variables:
        self.VisitorPanelLeft.photo = None
        self.VisitorPanelRight.photo = None

    def RegisterVisitor(self, event):
        nametagEnable = self.VisitorPanel.NametagToggle.GetValue()
        parentEnable = self.VisitorPanel.ParentToggle.GetValue()
        name = self.VisitorPanel.FirstName.GetValue()  #Required
        surname = self.VisitorPanel.Surname.GetValue() #Required
        phone = self.VisitorPanel.Phone.GetValue()     #Required
        invalid = False
        if name == '':
            self.VisitorPanel.FirstName.SetBackgroundColour('red')
            invalid = True
        if surname == '':
            self.VisitorPanel.Surname.SetBackgroundColour('red')
            invalid = True
        if phone == '':
            self.VisitorPanel.Phone.SetBackgroundColour('red')
            invalid = True
        if invalid:
            return 0
        paging = self.VisitorPanel.Paging.GetValue()   #(automatically generated)
        activity = self.activities[self.VisitorPanel.Activity.GetSelection()]
        medical = self.VisitorPanel.Medical.GetValue()
        #TODO: Parent linking
        parent = self.VisitorPanel.Parent1.GetValue()
        email = self.VisitorPanel.Email.GetValue()
        newsletter = self.VisitorPanel.NewsletterToggle.GetValue()
        neverExpires = self.VisitorPanel.NeverExpireToggle.GetValue()
        if neverExpires:
            expiration = None
        else:
            expiration = _wxdate2pydate(self.VisitorPanel.DatePicker.GetValue()).strftime('%Y-%m-%d')
        notifyExpires = self.VisitorPanel.NotifyWhenExpiresToggle.GetValue()

        room = self.VisitorPanel.Room.GetStringSelection()
        if room == '':  #No room assigned.
            room = None
        if room != None:
            #Convert it to an explicit id reference (I'd use GetSelection(), but the order might be wrong).
            room = self.db.GetRoomID(room)[0]

        if activity['parentTag'] == parentEnable:
            noParentTag = not(activity['parentTag'])
        else:
            noParentTag = not(parentEnable)

        print nametagEnable
        print parentEnable
        print name
        print surname
        print phone
        print paging
        print activity['name']
        print room
        print medical
        print parent
        print email
        print newsletter
        print expiration
        print notifyExpires
        print self.VisitorPanel.photo

        #Attempt to add record to database:
        try:
            self.db.Register(name, surname, phone, parent, paging=paging,
                mobileCarrier=0, activity=activity['id'], room=room,
                parentEmail=email, medical=medical, visitor=True,
                expiry=expiration, noParentTag=noParentTag, barcode=None,
                picture=self.VisitorPanel.photo,
                authorized=None, unauthorized=None, notes='')
            self.db.commit()
        except self.database.DatabaseError as e:
            if e.code == self.database.EMPTY_RESULT:
                wx.MessageBox('The record was unable to be added to the database.',
                              'Taxidi Database Error', wx.OK | wx.ICON_ERROR)

            return 0  #Don't close the panel

        #TODO: Add Visitor: Do printing if needed

        #Cleanup and close:
        self.VisitorPanel.photo = None
        self.CloseVisitorPanel(None)

    def ResetBackgroundColour(self, event):
        ctrl = event.GetEventObject()
        ctrl.SetBackgroundColour(wx.NullColour)

    def VisitorParentTab(self, event):
        if event.IsFromTab() and event.GetDirection(): #Direction is forward and caused by tab key
            self.VisitorPanel.Email.SetFocus()
        elif not event.GetDirection():
            self.VisitorPanel.Parent1.SetFocus()

    def VisitorParentFind(self, event):
        print "Find parent"
        pass

    def VisitorPhoto(self, evt):
        if conf.as_bool(conf.config['webcam']['enable']): #Webcam enabled?
            #Hide the visitor panel
            self.HideAll()
            if self.VisitorPanel.photo != None:
                #re-take; overwrite the old photo.
                self.WebcamPanel.SetOverwrite(self.VisitorPanel.photo)
            #Show the webcam input panel.
            self.ShowWebcamPanel(self.VisitorPhotoCancel, \
                self.VisitorPhotoSave, self.VisitorPhotoFile)
        else:
            #Just open a file selection dialog.
            path = os.path.abspath(os.path.expanduser(
                conf.config['webcam']['target']))
            dlg = ib.ImageDialog(self.frame, path)
            dlg.Centre()
            if dlg.ShowModal() == wx.ID_OK:
                if self.VisitorPanel.photo != None:
                    self.VisitorPanel.photo = \
                        self.PhotoStorage.saveImage(dlg.GetFile(),
                        int(self.VisitorPanel.photo))
                else:
                    self.VisitorPanel.photo = self.PhotoStorage.saveImage(dlg.GetFile())

                photoPath = self.PhotoStorage.getThumbnailPath(self.VisitorPanel.photo)
                #~ print "Resolves to file: {0}".format(photoPath)
                #Load and display new photo
                wximg = wx.Image(photoPath)
                wxbmp = wximg.ConvertToBitmap()
                self.VisitorPanel.ProfilePicture.SetBitmapLabel(wxbmp)

            else:
                #~ self.log.debug("> Dialogue cancelled.")
                pass

            dlg.Destroy()

    def VisitorPhotoFile(self, event):
        self.ShowVisitorPanel()
        self.CloseWebcamPanel()
        photo = self.WebcamPanel.GetFile()
        if self.VisitorPanel.photo != None:
            self.VisitorPanel.photo = self.PhotoStorage.saveImage(photo, \
                int(self.VisitorPanel.photo))
        else:
            self.VisitorPanel.photo = self.PhotoStorage.saveImage(photo)

        photoPath = self.PhotoStorage.getThumbnailPath(self.VisitorPanel.photo)
        print "Resolves to file: {0}".format(photoPath)
        #Load and display new photo
        wximg = wx.Image(photoPath)
        wxbmp = wximg.ConvertToBitmap()
        self.VisitorPanel.ProfilePicture.SetBitmapLabel(wxbmp)

    def VisitorPhotoSave(self, evt):
        photo = self.WebcamPanel.GetFile()
        print "Got photo ID: {0}".format(photo)
        self.VisitorPanel.photo = photo
        photoPath = self.PhotoStorage.getThumbnailPath(photo)
        print "Resolves to file: {0}".format(photoPath)
        self.ShowVisitorPanel()
        #Load and display new photo
        wximg = wx.Image(photoPath)
        wxbmp = wximg.ConvertToBitmap()
        self.VisitorPanel.ProfilePicture.SetBitmapLabel(wxbmp)
        self.CloseWebcamPanel()

    def VisitorPhotoCancel(self, evt):
        self.ShowVisitorPanel()
        self.CloseWebcamPanel()

    def VisitorDateChanged(self, evt):
        expirePeriod = int(conf.config['visitor']['expires'])
        self.VisitorPanel.Expires = _wxdate2pydate(self.VisitorPanel.DatePicker.GetValue())
        self.VisitorPanel.ExpiryText.SetLabel(self.VisitorPanel.Expires.strftime("%d %b %Y"))

    def CloseWebcamPanel(self):
        self.WebcamPanel.Unbind(webcam.CONTROLS_CANCEL)
        self.WebcamPanel.Unbind(webcam.CONTROLS_SAVE)
        self.WebcamPanel.Unbind(webcam.CONTROLS_SELECT_FILE)
        self.WebcamPanel.live.suspend()
        self.WebcamPanel.Hide()

    def ShowWebcamPanel(self, cancelFunction, saveFunction, fileFunction):
        self.WebcamPanel.Show()
        self.WebcamPanel.Bind(webcam.CONTROLS_CANCEL, cancelFunction)
        self.WebcamPanel.Bind(webcam.CONTROLS_SAVE, saveFunction)
        self.WebcamPanel.Bind(webcam.CONTROLS_SELECT_FILE, fileFunction)
        self.WebcamPanel.live.resume()
        pass

    def FormatEmailLive(self, event):
        email = event.GetEventObject()
        validate.EmailFormat(email)

    def FormatPhone(self, event):
        phone = event.GetEventObject()
        panel = phone.GetParent()
        validate.PhoneFormat(phone)
        if len(panel.Phone.GetValue()) > 4:
            panel.Paging.SetValue('{0}-{1}'.format(
                self.activities[panel.Activity.GetSelection()]['prefix'],
                phone.GetValue()[-4:]))

    def FormatPhoneLive(self, event):
        phone = event.GetEventObject()
        if phone.IsModified():
            validate.PhoneFormat(phone)
            panel = phone.GetParent()
            if len(panel.Phone.GetValue()) > 4:
                panel.Paging.SetValue('{0}-{1}'.format(
                    self.activities[panel.Activity.GetSelection()]['prefix'],
                    phone.GetValue()[-4:]))

    def FormatDateLive(self, event):
        dob = event.GetEventObject()
        if dob.IsModified():
            validate.DateFormat(dob)

    def FormatDate(self, event):
        dob = event.GetEventObject()
        validate.DateFormat(dob)
        #Set focus

    def FormatDatePost(self, event):
        dob = event.GetEventObject()
        validate.DateFormatPost(dob)


    def ToggleState(self, event):
        """
        Changes the background colour of a toggle button to `themeToggleColour` given
        the toggle's state.  Resets to system's default colour when off. Example usage:

            self.panel.MyToggle(wx.EVT_TOGGLEBUTTON, self.ToggleState)

        Useful to make toggle buttons more visible and easier to use.
        """
        btn = event.GetEventObject()
        if btn.GetValue():
            self.ToggleStateOn(btn) #Toggled on
        else:
            self.ToggleStateOff(btn) #Toggled off.

    def ToggleStateOn(self, btn):
        btn.SetValue(True)
        btn.SetBackgroundColour(themeToggleColour)

    def ToggleStateOff(self, btn):
        btn.SetValue(False)
        btn.SetBackgroundColour(wx.NullColor)

    def ToggleCheckBox(self, event):
        """
        Method for making toggle buttons behave more like large checkboxes.
        Sets the appropriate characters and text colour.
        """
        btn = event.GetEventObject()
        if btn.GetValue(): #Toggled on
            self.ToggleCheckBoxOn(btn)
        else: #Toggled off
            self.ToggleCheckBoxOff(btn)
        #Actions for each toggle:
        if btn == self.VisitorPanel.NeverExpireToggle:
            if btn.GetValue():
                self.VisitorPanel.DatePicker.Disable()
                self.VisitorPanel.ExpiryText.SetLabel('Never')
                self.VisitorPanel.Expires = None
            else:
                self.VisitorPanel.DatePicker.Enable()
                self.VisitorPanelSetExpiry()

    def ToggleCheckBoxOn(self, btn):
        btn.SetValue(True)
        btn.SetForegroundColour(themeCheckOnColour)
        btn.SetLabel(u'✔')

    def ToggleCheckBoxOff(self, btn):
        btn.SetValue(False)
        btn.SetForegroundColour(themeCheckOffColour)
        btn.SetLabel(u'✘')

    def VisitorPanelSetExpiry(self):
        today = date.today()
        self.VisitorPanel.CreatedText.SetLabel(today.strftime("%d %b %Y"))
        expirePeriod = int(conf.config['visitor']['expires'])
        if expirePeriod < 1:
            self.VisitorPanel.ExpiryText.SetLabel('Never')
            self.ToggleCheckBoxOn(self.VisitorPanel.NeverExpireToggle)
        else:
            self.VisitorPanel.Expires = today + relativedelta(days = expirePeriod)
            self.VisitorPanel.DatePicker.SetValue(_pydate2wxdate(self.VisitorPanel.Expires))
            self.VisitorPanel.ExpiryText.SetLabel(self.VisitorPanel.Expires.strftime("%d %b %Y"))

    def OnVisitor(self, event):
        #Setup the inputs, etc:
        self.activities = self.db.GetActivities() #Load activities from database
        self.ShowVisitorPanel() #Show the panel (Needed to set self.VisitorPanel)
        #Set the activity options:
        self.VisitorPanel.Activity.SetItems([ i['name'] for i in self.activities ])
        self.VisitorPanel.Activity.SetStringSelection(
            conf.config['config']['defaultActivity']) #Set default activity
        self.rooms = self.db.GetRooms()
        items = [ i['name'] for i in self.db.GetRoom(
            conf.config['config']['defaultActivity']) ]
        items.insert(0, '') #Allow blank selection
        self.VisitorPanel.Room.SetItems(items)
        self.VisitorPanel.Room.SetStringSelection('')

    def OnSelectActivity(self, event):
        choice = event.GetEventObject()
        panel = choice.GetParent()
        selection = event.GetString()
        #Set the rooms accordingly:
        items = [ i['name'] for i in self.db.GetRoom(selection) ]
        items.insert(0, '') #Allow blank selection
        panel.Room.SetItems(items)
        panel.Room.SetStringSelection('')
        #Reformat the paging number:
        if len(panel.Phone.GetValue()) > 4:
            panel.Paging.SetValue('{0}-{1}'.format(
                self.activities[event.GetSelection()]['prefix'],
                panel.Phone.GetValue()[-4:]))
        #Set the appropriate defaults for nametag settings:
        if self.activities[event.GetSelection()]['nametagEnable']:
            self.ToggleStateOn(panel.NametagToggle)
        else:
            self.ToggleStateOff(panel.NametagToggle)

        if self.activities[event.GetSelection()]['parentTagEnable']:
            self.ToggleStateOn(panel.ParentToggle)
        else:
            self.ToggleStateOff(panel.ParentToggle)

        #== VisitorPanel specific items ==
        #Set expire settings:
        if self.activities[event.GetSelection()]['autoExpire']:
            self.ToggleCheckBoxOff(self.VisitorPanel.NeverExpireToggle)
        else:
            self.ToggleCheckBoxOn(self.VisitorPanel.NeverExpireToggle)
            self.VisitorPanel.DatePicker.Disable()
        if self.activities[event.GetSelection()]['notifyExpire']:
            self.ToggleCheckBoxOn(self.VisitorPanel.NotifyWhenExpiresToggle)
        else:
            self.ToggleCheckBoxOff(self.VisitorPanel.NotifyWhenExpiresToggle)
        #Set newsletter default:
        if self.activities[event.GetSelection()]['newsletter']:
            self.ToggleCheckBoxOn(self.VisitorPanel.NewsletterToggle)
        else:
            self.ToggleCheckBoxOff(self.VisitorPanel.NewsletterToggle)

    def ShowVisitorPanel(self):
        self.HideAll()
        if self.user['leftHanded']:
            self.VisitorPanel = self.VisitorPanelLeft
        else:
            self.VisitorPanel = self.VisitorPanelRight

        self.VisitorPanel.Show()
        self.VisitorPanel.FirstName.SetFocus()
        today = date.today()
        self.VisitorPanel.CreatedText.SetLabel(today.strftime("%d %b %Y"))
        expirePeriod = int(conf.config['visitor']['expires'])
        if expirePeriod < 1:
            self.VisitorPanel.ExpiryText.SetLabel('Never')
            self.ToggleCheckBoxOn(self.VisitorPanel.NeverExpireToggle)
        else:
            self.VisitorPanel.Expires = today + relativedelta(days = expirePeriod)
            self.VisitorPanel.DatePicker.SetValue(_pydate2wxdate(self.VisitorPanel.Expires))
            self.VisitorPanel.ExpiryText.SetLabel(self.VisitorPanel.Expires.strftime("%d %b %Y"))

    def CloseVisitorPanel(self, event):
        #Reset displays and inputs
        self.VisitorPanel.ProfilePicture.SetBitmapLabel(self.NoPhoto128)
        self.VisitorPanel.FirstName.SetValue('')
        self.VisitorPanel.Surname.SetValue('')
        self.VisitorPanel.Phone.SetValue('')
        self.VisitorPanel.Phone.SetBackgroundColour(wx.NullColour)
        #~ self.VisitorPanel.PhoneCarrier.SetValue(0)
        self.VisitorPanel.Paging.SetValue('')
        #~ self.VisitorPanel.Activity.SetValue(0)
        self.VisitorPanel.Medical.SetValue('')
        self.VisitorPanel.Parent1.SetValue('')
        self.VisitorPanel.Email.SetValue('')
        self.VisitorPanel.Email.SetBackgroundColour(wx.NullColour)

        #Reset checkboxes:
        self.VisitorPanel.NametagToggle.SetValue(True)
        self.ToggleStateOn(self.VisitorPanel.NametagToggle)
        self.VisitorPanel.ParentToggle.SetValue(True)
        self.ToggleStateOn(self.VisitorPanel.ParentToggle)
        self.VisitorPanel.NewsletterToggle.SetValue(True)
        self.ToggleCheckBoxOn(self.VisitorPanel.NewsletterToggle)
        self.VisitorPanel.NeverExpireToggle.SetValue(False)
        self.ToggleCheckBoxOff(self.VisitorPanel.NeverExpireToggle)
        self.VisitorPanel.NotifyWhenExpiresToggle.SetValue(True)
        self.ToggleCheckBoxOn(self.VisitorPanel.NotifyWhenExpiresToggle)

        if self.VisitorPanel.photo != None:
            #remove the orphaned photo:
            self.PhotoStorage.delete(self.VisitorPanel.photo)

        #Reset variables and events:
        self.VisitorPanel.photo = None

        self.HideAll()
        self.ShowSearchPanel()

    def OnSearch(self, event):
        #Get what was typed in:
        query = self.Search.GetValue()
        if query == '2244':
            #Throw up some test data:
            self.ShowResultsPanel()
            results = [ {'name':'Johnathan Churchgoer', 'activity':'Explorers',  'room':'Jungle Room', 'status':taxidi.STATUS_NONE},
                    {'name':'Jane Smith',           'activity':'Explorers',  'room':'Ocean Room',  'status':taxidi.STATUS_CHECKED_IN},
                    {'name':'Joseph Flint',         'activity':'Outfitters', 'room':u'—',          'status':taxidi.STATUS_CHECKED_OUT, 'checkout-time':'11:46:34'} ]
            self.ResultsList.ShowResults(results)
        elif query == '9989':
            #Show single result:
            self.ShowRecordPanel()
        else:  #Bad query
            self.Search.SetBackgroundColour('red')
            self.Search.SetFocus()


    def ResetSearchColour(self, event):
        self.Search.SetBackgroundColour(wx.NullColour)


    def HideAll(self):
        """
        Hides all panels defined in self.panels
        """
        for i in self.panels:
            i.Hide()

    def ExitSearch(self, event):
        self.HideAll()
        self.MainMenu.Show()

    def BeginCheckinRoutine(self, event):
        self.MainMenu.Hide()
        self.ShowSearchPanel()

    def StartCheckin(self, event):
        conf.config.reload()
        self.setupDatabase()
        if self.PerformAuthentication(main=True):
            self.BeginCheckinRoutine(None)
        else:
            self.db.close()

    def ShowSearchPanel(self):
        if self.user['leftHanded']:
            self.LeftHandSearch.Show()
            self.SearchPanel = self.LeftHandSearch
        else:
            self.RightHandSearch.Show()
            self.SearchPanel = self.RightHandSearch
        self.SearchPanel.UserButton.SetLabel('Current User: %s' % self.user['user'])
        self.Search = self.SearchPanel.Search
        self.Search.Clear()
        self.Search.SetFocus()

    def SwitchUserDisable(self):
        self.LeftHandSearch.SwitchUserButton.Disable()
        self.RightHandSearch.SwitchUserButton.Disable()

    def SwitchUserEnable(self):
        self.LeftHandSearch.SwitchUserButton.Enable()
        self.RightHandSearch.SwitchUserButton.Enable()

    def SwitchUser(self, event):
        if conf.config['authentication']['method'].lower() == 'database':
            response = ''
            while response != None:
                response = dialogues.askLogin()
                if response[0] == self.user['user']:
                    #Already logged in.
                    response = None
                if response == None: break
                if self.db.AuthenticateUser(*response):
                    #Access granted
                    self.user = self.db.GetUser(response[0])
                    self.HideAll()
                    self.ShowSearchPanel()
                    self.SwitchUserEnable() #just in case
                    response = None
                else:
                    #Access denied
                    wx.MessageBox('Incorrect username or password.', 'Taxidi',
                        wx.OK | wx.ICON_EXCLAMATION)
            #Cancel action:
            self.Search.SetFocus()

    def ShowResultsPanel(self):
        self.ResultsPanel.opened = True
        self.HideAll()
        self.ResultsPanel.Show()

    def _excepthook (self, etype, value, tb) :
        if type is taxidi.Error:
            # application error - display a wx.MessageBox with the error message
            #wx.MessageBox()
            pass
        else:
            import sys, traceback
            xc = traceback.format_tb(tb)
            import wx.lib.dialogs
            msg = "Taxidi has encountered a program error.\n\n" \
                "Traceback:\n" + ''.join(xc)
            dlg = wx.lib.dialogs.ScrolledMessageDialog(self.frame, msg, "Program Traceback")
            dlg.ShowModal()

            dlg.Destroy()


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
        #~ self.Close()
        evt.Skip()  # Make sure the default handler runs too...

def showSplash():
    app = wx.PySimpleApp()
    splash = SplashScreen()
    splash.Show()
    app.MainLoop()

def _pydate2wxdate(date):
     import datetime
     assert isinstance(date, (datetime.datetime, datetime.date))
     tt = date.timetuple()
     dmy = (tt[2], tt[1]-1, tt[0])
     return wx.DateTimeFromDMY(*dmy)

def _wxdate2pydate(date):
     import datetime
     assert isinstance(date, wx.DateTime)
     if date.IsValid():
         ymd = map(int, date.FormatISODate().split('-'))
         return datetime.date(*ymd)
     else:
         return None

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
        import logging
        from wx import xrc
        import taxidi
        import conf
        import SearchResultsList
        import dialogues
        import hashlib
        import validate
        from datetime import date
        from dateutil.relativedelta import relativedelta

        if conf.as_bool(conf.config['webcam']['enable']) == True:
            import webcam
        else:
            #Import file selection dialogue instead
            import wx.lib.imagebrowser as ib
            import webcam #for maniuplating database photos

        try:
            app = MyApp(0)
            app.MainLoop()
        except:
            import sys, traceback
            xc = traceback.format_exception(*sys.exc_info())
            wx.MessageBox(''.join(xc))


#~ app = MyApp(0)
#~ app.MainLoop()
