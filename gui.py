#!/usr/bin/env python
#-*- coding:utf-8 -*-

#TODO: (URGENT DEADLINE 03.05) Create/add multi-service selection panel.
#TODO: (HIGH   DEADLINE 03.05) Integrate configuration, theme files.
#TODO: (URGENT DEADLINE 03.05) Add username/password dialogue.

#TODO: Make logging suck less
#TODO: Fix layout issues.  (Held together with duct tape right now.)
#TODO: Theme files.  Colours hard coded for now. (Probably something for conf.py)
#TODO: Set radiobutton background colours if possible.
#TODO: Clean up XML.
#TODO: Unify dual-name references (e.g. data['surname'] vs. data['lastname']
#       (According to database specification?)

#Couldn't get the wx-esque validator classes to work, so I wrote my own (validate.py)

#Imports for splash screen
import wx
import os
import signal

import traceback

__version__ = '0.70.10-dev'

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
        self.PhotoStorage = webcam.Storage() #Setup photo storage access
        self.jobID = 0 #jobID counter for forking print routine
        self.EmailJobID = 0 #jobID counter for sending email notifications
        self.multiJobID = 0 #For multiple check-in's.

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
        self.RegisterRight = xrc.XRCCTRL(self.frame, 'RegisterRight')
        self.RegisterLeft = xrc.XRCCTRL(self.frame, 'RegisterLeft')
        self.BarcodePanel = xrc.XRCCTRL(self.frame, 'BarcodePanel')
        self.DisplayPhotoPanel = xrc.XRCCTRL(self.frame, 'DisplayPhoto')
        if conf.as_bool(conf.config['webcam']['enable']):
            self.WebcamPanel = webcam.Panel(self.frame)
            self.setupWebcamPanel()

        #Setup panels
        self.setupMainMenu()
        self.setupSearch()
        self.setupRecordPanel()
        self.setupResultsList()
        self.setupVisitorPanel()
        self.setupRegisterPanel()
        self.setupBarcodePanel()
        self.setupDisplayPhotoPanel()

        #Setup programme menus:
        self.InitMenus()

        #Load generic icons
        self.NoPhoto480 = wx.Image(os.path.join(themeIconPath, 'no-photo-480.png')).ConvertToBitmap()
        self.NoPhoto128 = wx.Image(os.path.join(themeIconPath, 'no-photo-128.png')).ConvertToBitmap()
        self.NoPhoto100 = wx.Image(os.path.join(themeIconPath, 'no-photo-100.png')).ConvertToBitmap()

        #Bind events
        self.frame.Bind(wx.EVT_SIZE, self.on_size)

        self.frame.SetBackgroundColour(themeBackgroundColour)

        #Write background bitmap (will need to use ONPAINT event because OS X hates life).
        wximg = wx.Image(themeBanner)
        wxbanner=wximg.ConvertToBitmap()
        self.bitmap = wx.StaticBitmap(self.frame,-1,wxbanner,(0,0))


        #Put everything in a list for convenience when resizing, etc:
        self.panels =      ( self.MainMenu,
                             self.LeftHandSearch,   self.RightHandSearch,
                             self.RecordPanelLeft,  self.RecordPanelRight,
                             self.ResultsPanel,
                             self.VisitorPanelLeft, self.VisitorPanelRight,
                             self.RegisterLeft, self.RegisterRight,
                             self.BarcodePanel,
                             self.DisplayPhotoPanel )
        self.panelsLeft =  ( self.LeftHandSearch,  self.RecordPanelLeft,
                             self.VisitorPanelLeft, self.RegisterLeft )
        self.panelsRight = ( self.RightHandSearch, self.RecordPanelRight,
                             self.VisitorPanelRight, self.RegisterRight )

        for i in self.panels:
            i.SetBackgroundColour(themeBackgroundColour)
            i.SetForegroundColour(themeTextColour)

        #Hide all other panels:
        self.HideAll()
        self.MainMenu.Show()

        self.frame.Centre()
        self.frame.ShowFullScreen(conf.as_bool(conf.config['interface']['fullscreen']))
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
            self.WebcamPanel.CentreOnParent(dir=wx.BOTH)
        self.DisplayPhotoPanel.CentreOnParent(dir=wx.BOTH)


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
                raise
            except database.sqlite.OperationalError:
                wx.MessageBox('Unable to open database file:\n{0}'. \
                    format(datafile), 'Database Error', wx.OK | wx.ICON_ERROR)
                raise
            
        elif conf.config['database']['driver'].lower() == 'postgres':
            import dblib.postgres as database
            self.database = database
            try:
                self.db = database.Database(conf.config['database']['host'],
                                            conf.config['database']['database'],
                                            conf.config['database']['user'],
                                            conf.config['database']['pass'])
            except database.DatabaseError as e:
                if e.code == database.INVALID_PASSWORD:
                    wx.MessageBox("Invalid database username or password.",
                                  "Database Error", wx.OK | wx.ICON_ERROR)
                if e.code == database.FAIL:
                    #Unhandled database error.
                    wx.MessageBox("An unhandled database error occurred. "
                                  "The error was:\n\n{0}".format(e.error),
                                  "Database Error", wx.OK | wx.ICON_ERROR)
                raise  #Do not continue
                
        else:
            wx.MessageBox("Invalid database driver '{0}'.\n\nSelect "
                          "sqlite or postgres.".format(conf.config['database']['driver']),
                          u'Taxídí Error', wx.OK | wx.ICON_ERROR)
                
        if self.db.status == database.NEW:
            #The database was newly created
            wx.MessageBox('A new database was created at\n{0}\n Please '
                'confirm your configuration before continuing.'.format(datafile),
                'Taxidi', wx.OK | wx.ICON_INFORMATION)
        elif self.db.status == database.RESET_TABLES:
            wx.MessageBox('One or more database tables had to be created. '\
                'If this is not a first run then database integrity may be'\
                ' unstable.  Consult the documentation for more info.',
                'Notice', wx.OK | wx.ICON_INFORMATION)

        #Check that there's at least one activity, etc. defined:
        if len(self.db.GetActivities()) == 0:
            notify.warning('First run?', 'There are no activities defined. '\
                'Some features might not work as expected!\nPlease add at '\
                'least one activity before continuing.\n\nConsult the '\
                'documentation for more info.')
        if len(self.db.GetServices()) == 0:
            notify.warning('First run?', 'There are no services defined. '\
                'Some features will not work as expected!\nPlease add at '\
                'least one service before continuing.')

    def InitMenus(self):
        #Setup the programme menus
        self.frame.Bind(wx.EVT_MENU, self.OnAboutBox, id=xrc.XRCID("MenuAbout"))
        self.frame.Bind(wx.EVT_MENU, self.Quit, id=xrc.XRCID("MenuQuit"))

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
        self.MainMenu.Bind(wx.EVT_BUTTON, self.OnParentSearch, self.MainMenu.configure)
        self.MainMenu.Bind(wx.EVT_BUTTON, self.EditServices, self.MainMenu.services)
        #~ self.MainMenu.Bind(wx.EVT_BUTTON, self.EditActivities, self.MainMenu.activities)
        self.MainMenu.Bind(wx.EVT_BUTTON, self.OnAboutBox, self.MainMenu.about)
        self.MainMenu.Bind(wx.EVT_BUTTON, self.Quit, self.MainMenu.quit)

    def setupSearch(self):
        panels = (self.RightHandSearch, self.LeftHandSearch)

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
            pane.ServiceSelection = xrc.XRCCTRL(pane, 'ServiceSelection')
            pane.ClearButton = xrc.XRCCTRL(pane, 'ClearButton')
            pane.SearchButton = xrc.XRCCTRL(pane, 'SearchButton')
            pane.RegisterButton = xrc.XRCCTRL(pane, 'RegisterButton')
            pane.VisitorButton = xrc.XRCCTRL(pane, 'VisitorButton')
            pane.BusMinistryButton = xrc.XRCCTRL(pane, 'BusMinistryButton')
            pane.SwitchUserButton = xrc.XRCCTRL(pane, 'SwitchUserButton')
            pane.StatisticsButton = xrc.XRCCTRL(pane, 'StatisticsButton')
            pane.EmergencyListButton = xrc.XRCCTRL(pane, 'EmergencyListButton')
            pane.ExitButton = xrc.XRCCTRL(pane, 'ExitButton')
            
            pane.Search.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
            pane.ServiceSelection.Bind(wx.EVT_CHOICE, self.OnChangeService)
            pane.Search.Bind(wx.EVT_TEXT, self.ResetSearchColour)
            pane.ClearButton.Bind(wx.EVT_BUTTON, self.clearSearchEvent)
            pane.SearchButton.Bind(wx.EVT_BUTTON, self.OnSearch)
            pane.RegisterButton.Bind(wx.EVT_BUTTON, self.OnRegister)
            pane.VisitorButton.Bind(wx.EVT_BUTTON, self.OnVisitor)
            pane.SwitchUserButton.Bind(wx.EVT_BUTTON, self.SwitchUser)
            pane.StatisticsButton.Bind(wx.EVT_BUTTON, self.ShowStatistics)
            pane.ExitButton.Bind(wx.EVT_BUTTON, self.ExitSearch)
            pane.BusMinistryButton.Bind(wx.EVT_BUTTON, self.BusMinistry)


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

    def ShowStatistics(self, event):    
        self.setupStatisticsDialog()
        self.StatFrame.ShowModal()
        self.StatFrame.Destroy()
        
    def setupStatisticsDialog(self):
        self.StatFrame = self.res.LoadDialog(self.frame, 'StatisticsDialog')
        self.StatFrame.Service = xrc.XRCCTRL(self.StatFrame, 'Service')
        self.StatFrame.Activity = xrc.XRCCTRL(self.StatFrame, 'Activity')
        self.StatFrame.Room = xrc.XRCCTRL(self.StatFrame, 'Room')
        self.StatFrame.TotalText = xrc.XRCCTRL(self.StatFrame, 'TotalText')
        self.StatFrame.MembersText = xrc.XRCCTRL(self.StatFrame, 'MembersText')
        self.StatFrame.VisitorsText = xrc.XRCCTRL(self.StatFrame, 'VisitorsText')
        self.StatFrame.VolunteersText = xrc.XRCCTRL(self.StatFrame, 'VolunteersText')
        
        self.StatFrame.PrintButton = xrc.XRCCTRL(self.StatFrame, 'PrintButton')
        self.StatFrame.SaveButton = xrc.XRCCTRL(self.StatFrame, 'SaveButton')
        self.StatFrame.RefreshButton = xrc.XRCCTRL(self.StatFrame, 'RefreshButton')
        self.StatFrame.CloseButton = xrc.XRCCTRL(self.StatFrame, 'CloseButton')
        
        self.StatFrame.CloseButton.Bind(wx.EVT_BUTTON, self.CloseStatisticsDialog)
        
        services = [u'— Any —']
        services.extend([ i['name'] for i in self.services ])
        self.StatFrame.Service.SetItems(services)
        self.StatFrame.Service.SetSelection(0)
        
        self.activities = self.db.GetActivities()
        activities = [u'— Any —']
        activities.extend([ i['name'] for i in self.activities ])
        self.StatFrame.Activity.SetItems(activities)
        self.StatFrame.Activity.SetSelection(0)
        
        self.rooms = self.db.GetRooms()
        rooms = [u'— Any —']
        rooms.extend([ i['name'] for i in self.rooms ])
        self.StatFrame.Room.SetItems(rooms)
        self.StatFrame.Room.SetSelection(0)
        
    def CloseStatisticsDialog(self, event):
        self.StatFrame.Destroy()
        
    def BusMinistry(self, event):
        driverName = ""
        dlNumber = ""
        labelText = "0"
        
        dlg = dialogues.BusDialog(self.frame, wx.ID_ANY)
        while driverName == "" or dlNumber == "" or labelText == "":
            dlg.SetPosition((0, self.frame.GetPosition()[1] + 100))
            dlg.CentreOnParent(wx.HORIZONTAL)
            ret = dlg.ShowModal()
            if ret == wx.ID_CANCEL:
                dlg.Destroy()
                return
            #Read values. Loop will exit when all values are non-blank
            driverName = dlg.GetNameValue()
            dlNumber = dlg.GetDLValue()
            labelText = dlg.GetLabelsValue()
            if not labelText.isdigit(): labelText = ""
        dlg.Destroy()
        
        #Select default activity per config file
        self.activities = self.db.GetActivities()
        defaultActivity = conf.config['config']['defaultActivity']
        
        #Most confusing usage of dictionary list comprehension. Probably a better way
        try:
            activity = self.activities[[ act['name'] for act in self.activities ].index(defaultActivity)]
        except ValueError:
            notify.error("Configuration Error", 
                "The default activity {0} does not exist.".format(defaultActivity))
        
        #Generate secure code if needed
        if activity['securityTag']:
            if conf.as_bool(conf.config['config']['secureCodeRemote']):
                #Use remote
                code_generator = taxidi.SecureCode(conf.config['config']['secureCodeURI'])
            else:
                code_generator = taxidi.SecureCode() #Use local generator
            secure = code_generator.request() #Draw a code
            del code_generator #TODO: put generator initialization in BeginCheckinRoutine

            #Hash secure mode if needed
            if activity['securityMode'].lower() == 'simple':
                parentSecure = secure
            elif activity['securityMode'].lower() == 'md5':
                parentSecure = secure
                import hashlib
                secure = hashlib.md5(secure).hexdigest()[:4].upper()
        else:
            secure = None
            parentSecure = None
        
        #Produce blank name tag with security code
        trash = []
        if secure == None:
            barcode = False
        else:
            barcode = True
        #Generate the nametag:
        self.printing.nametag(theme=activity['nametag'], code='BUS',
                              first='&nbsp;',
                              last=driverName, room=dlNumber,
                              secure=secure, barcode=barcode)
        
        if conf.as_bool(conf.config['printing']['preview']):
            #Open print preview
            self.printing.preview()
            trash.append(self.printing.pdf) #Delete it later
            
        #Print enough labels for everyone
        for i in range(int(labelText)):
            if conf.as_bool(conf.config['printing']['enable']):
                if conf.config['printing']['printer'] == '':
                    self.printing.printout() #Use default printer
                else:
                    #TODO: do validation against printer name.
                    self.printing.printout(printer=conf.config['printing']['printer'])
        
        
        #Print one security receipt
        if secure != None:
            barcode = False
        else:
            barcode = True
        link = activity['parentURI']
        self.printing.parent(theme=activity['nametag'], 
                             code='BUS', secure=parentSecure, link=link)
        if conf.as_bool(conf.config['printing']['preview']):
            #Open preview
            self.printing.preview()
            trash.append(self.printing.pdf)
        #Do printing if needed
        for i in range(int(labelText)):
            if conf.as_bool(conf.config['printing']['enable']):
                if conf.config['printing']['printer'] == '':
                    self.printing.printout() #Use default printer
                else:
                    #TODO: do validation against printer name.
                    self.printing.printout(printer=conf.config['printing']['printer'])

        wx.CallLater(1000, self.printing.cleanup, trash) #Delete temporary files later
        
        #TODO: FIXME: Insert into database marking the current service
        

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

    def setupBarcodePanel(self):
        pane = self.BarcodePanel
        #Inputs:
        pane.code1 = xrc.XRCCTRL(pane, 'code1')
        pane.code2 = xrc.XRCCTRL(pane, 'code2')
        pane.code3 = xrc.XRCCTRL(pane, 'code3')
        pane.code4 = xrc.XRCCTRL(pane, 'code4')
        pane.code5 = xrc.XRCCTRL(pane, 'code5')
        pane.code6 = xrc.XRCCTRL(pane, 'code6')
        pane.codes = ( pane.code1, pane.code2, pane.code3, pane.code4, pane.code5, pane.code6 )
        #Clear buttons:
        pane.clear1 = xrc.XRCCTRL(pane, 'clear1')
        pane.clear2 = xrc.XRCCTRL(pane, 'clear2')
        pane.clear3 = xrc.XRCCTRL(pane, 'clear3')
        pane.clear4 = xrc.XRCCTRL(pane, 'clear4')
        pane.clear5 = xrc.XRCCTRL(pane, 'clear5')
        pane.clear6 = xrc.XRCCTRL(pane, 'clear6')
        pane.buttons = ( pane.clear1, pane.clear2, pane.clear3, pane.clear4, pane.clear5, pane.clear6 )
        for i in pane.buttons:
            i.Bind(wx.EVT_BUTTON, self.clearBarcode)
        #Command buttons:
        pane.save = xrc.XRCCTRL(pane, 'BarcodeSave')
        pane.save.Bind(wx.EVT_BUTTON, self.saveBarcodes)
        pane.cancel = xrc.XRCCTRL(pane, 'BarcodeCancel')
        pane.cancel.Bind(wx.EVT_BUTTON, self.hideBarcodePanel)
        #Variables:
        pane.barcodes = []
        #Set size:
        pane.SetSize((1024, 540))

    def clearBarcode(self, event):
        #Clear the value in the corresponding text entry
        button = event.GetEventObject()
        pane = button.GetParent()
        index = pane.buttons.index(button)
        pane.codes[index].SetValue('')
        pane.codes[index].SetFocus()

    def saveBarcodes(self, event):
        pane = event.GetEventObject().GetParent()
        pane.barcodes = []
        for inp in pane.codes:
            pane.barcodes.append(inp.GetValue())
        print pane.barcodes
        pane.Hide()

    def showBarcodePanel(self, event=None):
        self.BarcodePanel.Show()
        self.BarcodePanel.code1.SetFocus()

    def hideBarcodePanel(self, event=None):
        self.BarcodePanel.Hide()

    def setupDisplayPhotoPanel(self):
        pane = self.DisplayPhotoPanel
        pane.CentreOnParent(dir=wx.BOTH)
        pane.photo = xrc.XRCCTRL(pane, 'photo')
        pane.cancel = xrc.XRCCTRL(pane, 'PhotoCancel')
        pane.cancel.Bind(wx.EVT_BUTTON, self.ClosePhotoPanel)
        pane.retake = xrc.XRCCTRL(pane, 'PhotoRetake')
        pane.retake.Bind(wx.EVT_BUTTON, self.RecordPhoto)

    def setupRecordPanel(self):
        panels = (self.RecordPanelLeft, self.RecordPanelRight)
        self.RecordPanel = self.RecordPanelRight

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
            pane.Phone = xrc.XRCCTRL(pane, 'Phone')
            pane.FirstName = xrc.XRCCTRL(pane, 'Name')
            pane.Surname = xrc.XRCCTRL(pane, 'Surname')
            pane.Grade = xrc.XRCCTRL(pane, 'Grade')
            pane.PhoneCarrier = xrc.XRCCTRL(pane, 'PhoneCarrier')
            pane.Paging = xrc.XRCCTRL(pane, 'Paging')
            pane.Activity = xrc.XRCCTRL(pane, 'Activity')
            pane.Room = xrc.XRCCTRL(pane, 'Room')
            pane.Medical = xrc.XRCCTRL(pane, 'Medical')
            pane.Parent1 = xrc.XRCCTRL(pane, 'Parent1')
            pane.Parent2 = xrc.XRCCTRL(pane, 'Parent2')
            pane.Email = xrc.XRCCTRL(pane, 'Email')
            pane.Notes = xrc.XRCCTRL(pane, 'Notes')
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
            pane.AlertButton = xrc.XRCCTRL(pane, 'AlertButton')
            pane.BarcodeButton = xrc.XRCCTRL(pane, 'BarcodeButton')
            pane.PhoneButton = xrc.XRCCTRL(pane, 'PhoneButton')
            pane.PagingButton = xrc.XRCCTRL(pane, 'PagingButton')
            pane.Parent1Find = xrc.XRCCTRL(pane, 'Parent1Find')
            pane.Parent2Find = xrc.XRCCTRL(pane, 'Parent2Find')
            pane.AuthorizePickupButton = xrc.XRCCTRL(pane,
                'AuthorizePickupButton')
            pane.DenyPickupButton = xrc.XRCCTRL(pane, 'DenyPickupButton')
            pane.EmergencyContactButton = xrc.XRCCTRL(pane,
                'EmergencyContactButton')
            pane.HistoryButton = xrc.XRCCTRL(pane, 'HistoryButton')
            pane.DeleteButton = xrc.XRCCTRL(pane, 'DeleteButton')
            pane.PrintNametagButton = xrc.XRCCTRL(pane, 'ReprintNametag')

            pane.ProfilePicture.Bind(wx.EVT_BUTTON, self.ShowPhotoPanel)
            pane.CloseButton.Bind(wx.EVT_BUTTON, self.CloseRecordPanel)
            pane.NametagToggle.Bind(wx.EVT_TOGGLEBUTTON, self.ToggleState)
            pane.ParentToggle.Bind(wx.EVT_TOGGLEBUTTON, self.ToggleState)
            pane.CheckinButton.Bind(wx.EVT_BUTTON, self.SaveRecord)
            pane.MultiServiceButton.Bind(wx.EVT_BUTTON, self.SaveRecord)
            pane.SaveButton.Bind(wx.EVT_BUTTON, self.SaveRecord)
            pane.AlertButton.Bind(wx.EVT_BUTTON, self.ShowAlertDialog)
            pane.BarcodeButton.Bind(wx.EVT_BUTTON, self.showBarcodePanel)
            pane.PagingButton.Bind(wx.EVT_BUTTON, self.SetPagingCode)
            pane.Activity.Bind(wx.EVT_CHOICE, self.OnSelectActivity)
            pane.Parent1.Bind(wx.EVT_TEXT_ENTER, self.OnParentSearch)
            pane.Parent1Find.Bind(wx.EVT_BUTTON, self.OnParentSearch)
            pane.Email.Bind(wx.EVT_TEXT, self.FormatEmailLive)
            pane.Phone.Bind(wx.EVT_KILL_FOCUS, self.FormatPhone)
            pane.Phone.Bind(wx.EVT_TEXT, self.FormatPhoneLive)
            pane.FirstName.Bind(wx.EVT_TEXT, self.ResetBackgroundColour)
            pane.Surname.Bind(wx.EVT_TEXT, self.ResetBackgroundColour)
            pane.HistoryButton.Bind(wx.EVT_BUTTON, self.ShowHistory)
            pane.DeleteButton.Bind(wx.EVT_BUTTON, self.OnDeleteRecord)
            pane.PrintNametagButton.Bind(wx.EVT_BUTTON, self.PrintNametag)
            
    def ShowHistory(self, event):
        panel = event.GetEventObject().GetParent()
        history = self.db.GetHistory(panel.data['id'])
        dlg = dialogues.HistoryDialog(self.frame, wx.ID_ANY, history, panel.data)
        dlg.ShowModal()
        #~ dlg.Destroy()  #FIXME: This causes a segfault for some reason
        
    def PrintNametag(self, event):
        panel = event.GetEventObject().GetParent()
        nametagEnable = panel.NametagToggle.GetValue()
        parentEnable = panel.ParentToggle.GetValue()
        name = panel.FirstName.GetValue()  #Required
        surname = panel.Surname.GetValue() #Required
        paging = panel.Paging.GetValue()     #Required
        medical = panel.Medical.GetValue()
        activity = self.activities[panel.Activity.GetSelection()]
        data = { 'id': panel.data['id'], 'name': name, 'surname': surname,
                     'paging': paging, 'medical': medical,
                     'room': panel.Room.GetStringSelection(),
                     'activity': activity, 'nametag': nametagEnable,
                     'parentTag': parentEnable }
        self.DoCheckin((self.service['name'],), data, printOnly=True)
        notify.info("Re-printing nametags, please wait....", "Taxidi")

    def ShowPhotoPanel(self, event):
        self.DisplayPhotoPanel.ParentObject = event.GetEventObject().GetParent()
        if self.DisplayPhotoPanel.ParentObject == self.RecordPanel:
            self.HideAll()
            if self.RecordPanel.data['picture'] != None and \
              str(self.RecordPanel.data['picture']) != 'None':
                try:
                #Load and set the profile picture:
                    path = self.PhotoStorage.getImagePath(self.RecordPanel.data['picture'])
                    bmp = wx.Image(path).ConvertToBitmap()
                    self.DisplayPhotoPanel.photo.SetBitmap(bmp)
                except:
                    wx.MessageBox('Unable to load photo for this record.',
                                  'Taxidi Error', wx.OK | wx.ICON_ERROR)
                    self.DisplayPhotoPanel.photo.SetBitmap(self.NoPhoto480)
            else:
                self.DisplayPhotoPanel.photo.SetBitmap(self.NoPhoto480)
        elif self.DisplayPhotoPanel.ParentObject == self.ResultsControls:
            self.HideAll()
            self.DisplayPhotoPanel.retake.Hide()
            selected = self.ResultsList.selected
            if selected == None: selected = 0
            print self.ResultsList.results[selected]
            if self.ResultsList.results[selected]['picture'] != None and \
              self.ResultsList.results[selected]['picture'] != 'None':
                #Load and set the profile picture:
                try:
                    f = open(self.PhotoStorage.getImagePath(self.ResultsList.results[selected]['picture']))
                    f.close()
                    path = self.PhotoStorage.getImagePath(self.ResultsList.results[selected]['picture'])
                    bmp = wx.Image(path).ConvertToBitmap()
                    self.DisplayPhotoPanel.photo.SetBitmap(bmp)
                except IOError:
                    print "Not found: ", self.ResultsList.results[selected]['picture']
                    self.DisplayPhotoPanel.photo.SetBitmap(self.NoPhoto480)
            else:
                self.DisplayPhotoPanel.photo.SetBitmap(self.NoPhoto480)
        self.DisplayPhotoPanel.Show()

    def ClosePhotoPanel(self, event):
        self.DisplayPhotoPanel.Hide()
        if self.DisplayPhotoPanel.ParentObject == self.RecordPanel:
            self.ShowRecordPanel()
        elif self.DisplayPhotoPanel.ParentObject == self.ResultsControls:
            self.DisplayPhotoPanel.retake.Show()
            self.ShowResultsPanel()

    def CloseRecordPanel(self, event):
        self.RecordPanel.ProfilePicture.SetBitmapLabel(self.NoPhoto128)
        self.RecordPanelLeft.Hide()
        self.RecordPanelRight.Hide()
        if self.ResultsPanel.opened:
            self.ShowResultsPanel()
        else:
            self.ShowSearchPanel()

    def ShowAlertDialog(self, event):
        #Load the alert frame:
        self.AlertDialog = self.res.LoadDialog(None, 'AlertDialog')
        #Setup controls and bindings:
        self.AlertDialog.Cancel = xrc.XRCCTRL(self.AlertDialog, 'AlertCancel')
        self.AlertDialog.Send = xrc.XRCCTRL(self.AlertDialog, 'AlertSend')
        self.AlertDialog.Message = xrc.XRCCTRL(self.AlertDialog, 'AlertMessage')
        self.AlertDialog.NotifyParent = xrc.XRCCTRL(self.AlertDialog, 'NotifyParent')
        self.AlertDialog.NotifyTech = xrc.XRCCTRL(self.AlertDialog, 'NotifyTech')
        self.AlertDialog.NotifyAdmin = xrc.XRCCTRL(self.AlertDialog, 'NotifyAdmin')
        self.AlertDialog.SMSRecipients = xrc.XRCCTRL(self.AlertDialog, 'SMSRecipients')

        self.AlertDialog.Cancel.Bind(wx.EVT_BUTTON, self.CloseAlert)
        self.AlertDialog.Send.Bind(wx.EVT_BUTTON, self.SendAlert)
        
        #Set data:
        button = event.GetEventObject()
        parent = button.GetParent()
        
        #Update data from form:
        parent.data['phone'] = parent.Phone.GetValue()
        parent.data['name'] = parent.FirstName.GetValue()
        parent.data['lastname'] = parent.Surname.GetValue()
        parent.data['paging'] = parent.Paging.GetValue()
        self.AlertDialog.data = parent.data
        self.AlertDialog.activity = self.activities[parent.data['activity']-1]
        message = self.AlertDialog.activity['alertText']
        if message == None:
            #Use default from config as fallback.
            message = conf.config['notifications']['message']
        message = message.replace('{code}', parent.data['paging'])
        message = message.replace('{name}', parent.data['name'])
        message = message.replace('{lastname}', parent.data['lastname'])
        message = message.replace('{activity}', self.AlertDialog.activity['name'])
        message = message.replace('{room}', self.db.GetRoomByID(parent.data['room']))
        if parent.data['mobileCarrier'] == 0 or None:
            self.SetAlertData(message, None, []) #Number is landline
        else:
            self.SetAlertData(message, parent.data['phone'], []) #Number is landline
        
        #Show the dialog
        print self.AlertDialog.ShowModal()

    def SetAlertData(self, message, parent, recipients):
        """
        Sets data for the alert dialog.
        `message`: Alert message to send
        `parent`: Formatted mobile phone number to send SMS alert to.
                  None for land-line.
        `recipients`: List of additinoal formatted phone numbers to send
                      alerts to.
        """
        self.AlertDialog.Message.SetValue(str(message))
        if parent != None:
            self.AlertDialog.NotifyParent.SetLabel("SMS Parent: {0}".format(parent))
            self.AlertDialog.NotifyParent.SetValue(True)
            self.AlertDialog.NotifyParent.Enable()
        else:
            self.AlertDialog.NotifyParent.SetLabel("(Unavailable)")
            self.AlertDialog.NotifyParent.SetValue(False)
            self.AlertDialog.NotifyParent.Disable()
        
        self.AlertDialog.parent = parent
        
        self.AlertDialog.SMSRecipients.SetItems(recipients)
        #~ for i in recipients:
        self.AlertDialog.SMSRecipients.SetCheckedStrings(recipients)
            
        if conf.as_bool(conf.config['notifications']['techbooth']):
            self.AlertDialog.NotifyTech.Enable()
            self.AlertDialog.NotifyTech.SetValue(True)
        else:
            self.AlertDialog.NotifyTech.Disable()
        
        #~ self.AlertDialog.NotifyAdmin.SetValue(True)
        self.AlertDialog.NotifyAdmin.Disable() #Unimplemented for now
        
    def SendAlert(self, event):
        button = event.GetEventObject()
        panel = button.GetParent()
        print "Got button and panel object"
        message = panel.Message.GetValue()
        print message
        if panel.NotifyParent.GetValue():
            recipients = [ panel.parent ] #Parent number on SMS list
        else:
            recipients = []
        recipients.append(panel.SMSRecipients.GetCheckedStrings())
        
        panel.Destroy() #Close panel
        #TODO: Send alerts
            #Get growl/openLP data for tech/activity admin
            #Get phone number for tech/activity admin
            #Get notifo keys/passes
        notify.info("Sending Alert",
                "Sending alert for {0}.".format(panel.data['paging']))
                
        if panel.NotifyTech.GetValue(): #Notify tech booth
            #Since the notifo service is no longer available, we'll use email
            email = conf.config['notifications']['techboothEmail'] 
            location = conf.config['config']['name']
            subject = conf.config['notifications']['techboothSubject']
            if conf.as_bool(conf.config['notifications']['techbooth']) and email != '':
                print "Starting email producer"
                #send the contents of `message`
                self.EmailJobID += 1
                delayedresult.startWorker(self._EmailAlertConsumer,
                    self._EmailAlertProducer,
                    wargs=(self.EmailJobID, email, location, subject, message),
                    jobID=self.EmailJobID)
                
        #Send SMS alert to recipients
        if panel.NotifyParent.GetValue():
            self._smsProducer(None, recipients, message)
            
    def _smsProducer(self, jobID, recipients, message):
        if hasattr(self, 'smsDriver') == False:
            from notify import sms
            try:
                self.smsDriver = sms.SMS(notifyEnable=True, 
                                     user=conf.config['notifications']['email'], 
                                     passwd=conf.config['notifications']['password'])
            except sms.LoginError:
                notify.error("Notification Error", "Unable to login to GoogleVoice.")
                return jobID
        self.smsDriver.sendMany(recipients, message)
        return jobID
                
    def CloseAlert(self, event):
        self.AlertDialog.Destroy()
        
    def ShowErrorDialogue(self, message):
        dlg = wx.MessageDialog(self.frame, message, "Taxidi Error", wx.OK|wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()

    def _EmailAlertConsumer(self, delayedResult):
        jobID = delayedResult.getJobID()
        assert jobID == self.EmailJobID
        try:
            result = delayedResult.get()
        except Exception, exc:
            print exc
            wx.CallAfter(self.ShowErrorDialogue, 
                "Result for job %s raised exception:\n%s.\n\nThe alert may not have been sent." % (jobID, exc))
            return

    def _EmailAlertProducer(self, JobID, to, fromText, subject, message):
        import mail
        print "Sending email"
        mail.send(to, fromText, subject, message)
        return JobID
    

    def SetPagingCode(self, event):
        btn = event.GetEventObject()
        panel = btn.GetParent()
        if len(panel.Phone.GetValue()) > 4:
            panel.Paging.SetValue('{0}-{1}'.format(
                self.activities[event.GetSelection()]['prefix'],
                panel.Phone.GetValue()[-4:]))

    def OnDeleteRecord(self, event):
        data = self.RecordPanel.data
        dlg = wx.MessageBox('Are you sure you want to delete this record?\n' \
            '(Name: {0} {1})'.format(data['name'], data['lastname']),
            'Please Confirm', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
        if dlg == wx.YES:
            try:
                self.db.Delete(data['id']) #Delete the record
                self.db.commit() #commit to the database
            except:  #TODO: Catch the proper errors
                wx.MessageBox('Error while deleting record.', 'Database Error',
                               wx.ICON_ERROR | wx.OK)
                return 1
            #Remove their photo if needed:
            if data['picture'] != None:
                self.PhotoStorage.delete(data['picture'])
            #Remove their barcodes, if any:
            try:
                self.db.RemoveAllBarcodes(data['id'])
                self.db.commit()
            except self.database.DatabaseError as e:
                wx.MessageBox('Error while removing barcodes for record {0}.\n'
                              'The error was: {1}'.format(data['id'], e),
                              'Database Error', wx.ICON_ERROR | wx.OK)

            self.CloseRecordPanel(None)
            #If the results list was open, remove the deleted record:
            if self.ResultsPanel.opened:
                #Remove from the results vector:
                self.ResultsList.results.pop(self.ResultsList.selected)
                #If there's nothing left in the list, close the search results:
                if len(self.ResultsList.results) == 0:
                    self.CloseResults(None)
                else:
                    #Refresh the list:
                    self.ResultsList.DeleteAllItems()
                    self.ResultsList.ShowResults(self.ResultsList.results)


    def ShowRegisterPanel(self, event=None):
        if self.user['leftHanded']:
            self.RegisterLeft.Show()
            self.RegisterPanel = self.RegisterLeft
        else:
            self.RegisterRight.Show()
            self.RegisterPanel = self.RegisterRight

    def setupRegisterPanel(self):
        panels = (self.RegisterRight, self.RegisterLeft)
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
            pane.Phone = xrc.XRCCTRL(pane, 'Phone')
            pane.FirstName = xrc.XRCCTRL(pane, 'Name')
            pane.Surname = xrc.XRCCTRL(pane, 'Surname')
            pane.Grade = xrc.XRCCTRL(pane, 'Grade')
            pane.PhoneCarrier = xrc.XRCCTRL(pane, 'PhoneCarrier')
            pane.Paging = xrc.XRCCTRL(pane, 'Paging')
            pane.Activity = xrc.XRCCTRL(pane, 'Activity')
            pane.Room = xrc.XRCCTRL(pane, 'Room')
            pane.Medical = xrc.XRCCTRL(pane, 'Medical')
            pane.Parent1 = xrc.XRCCTRL(pane, 'Parent1')
            pane.Parent2 = xrc.XRCCTRL(pane, 'Parent2')
            pane.Email = xrc.XRCCTRL(pane, 'Email')
            pane.Notes = xrc.XRCCTRL(pane, 'Notes')
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

            pane.ProfilePicture.Bind(wx.EVT_BUTTON, self.RegisterPhoto)
            pane.BarcodeButton.Bind(wx.EVT_BUTTON, self.showBarcodePanel)
            pane.Activity.Bind(wx.EVT_CHOICE, self.OnSelectActivity)
            pane.Email.Bind(wx.EVT_TEXT, self.FormatEmailLive)
            pane.Phone.Bind(wx.EVT_KILL_FOCUS, self.FormatPhone)
            pane.Phone.Bind(wx.EVT_TEXT, self.FormatPhoneLive)
            pane.FirstName.Bind(wx.EVT_TEXT, self.ResetBackgroundColour)
            pane.Surname.Bind(wx.EVT_TEXT, self.ResetBackgroundColour)
            pane.CloseButton.Bind(wx.EVT_BUTTON, self.CloseRegisterPanel)
            pane.SaveButton.Bind(wx.EVT_BUTTON, self.OnRegisterSave)
            pane.CheckinButton.Bind(wx.EVT_BUTTON, self.OnRegisterSave)

            pane.NametagToggle.SetBackgroundColour(themeToggleColour) #On by default
            pane.NametagToggle.Bind(wx.EVT_TOGGLEBUTTON, self.ToggleState)
            pane.ParentToggle.SetBackgroundColour(themeToggleColour)  #On by default
            pane.ParentToggle.Bind(wx.EVT_TOGGLEBUTTON, self.ToggleState)

        #Set some default variables:
        for pane in panels:
            pane.photo = None

    def CloseRegisterPanel(self, event):
        self.RegisterPanel.ProfilePicture.SetBitmapLabel(self.NoPhoto128)
        self.RegisterPanel.FirstName.SetValue('')
        self.RegisterPanel.Surname.SetValue('')
        self.RegisterPanel.Grade.SetValue('')
        self.RegisterPanel.Phone.SetValue('')
        self.RegisterPanel.Phone.SetBackgroundColour(wx.NullColour)
        #~ self.RegisterPanel.PhoneCarrier.SetValue(0)
        self.RegisterPanel.Paging.SetValue('')
        #~ self.RegisterPanel.Activity.SetValue(0)
        self.RegisterPanel.Medical.SetValue('')
        self.RegisterPanel.Parent1.SetValue('')
        self.RegisterPanel.Parent2.SetValue('')
        self.RegisterPanel.Notes.SetValue('')
        self.RegisterPanel.DOB.SetValue('YYYY-MM-DD')
        self.RegisterPanel.DOB.SetBackgroundColour(wx.NullColour)
        self.RegisterPanel.DOB.SetForegroundColour('grey')
        self.RegisterPanel.Email.SetValue('')
        self.RegisterPanel.Email.SetBackgroundColour(wx.NullColour)

        #Reset checkboxes:
        self.RegisterPanel.NametagToggle.SetValue(True)
        self.ToggleStateOn(self.RegisterPanel.NametagToggle)
        self.RegisterPanel.ParentToggle.SetValue(True)
        self.ToggleStateOn(self.RegisterPanel.ParentToggle)

        if self.RegisterPanel.photo != None:
            #remove the orphaned photo:
            self.PhotoStorage.delete(self.RegisterPanel.photo)

        #Reset variables and events:
        self.RegisterPanel.photo = None
        self.HideAll()
        self.ShowSearchPanel()

    def OnRegisterSave(self, event):
        button = event.GetEventObject()
        panel = button.GetParent()
        nametagEnable = panel.NametagToggle.GetValue()
        parentEnable = panel.ParentToggle.GetValue()
        name = panel.FirstName.GetValue()  #Required
        surname = panel.Surname.GetValue() #Required
        phone = panel.Phone.GetValue()     #Required
        carrier = panel.PhoneCarrier.GetSelection()
        invalid = False
        if name == '':
            panel.FirstName.SetBackgroundColour('red')
            invalid = True
        if surname == '':
            panel.Surname.SetBackgroundColour('red')
            invalid = True
        if phone == '':
            panel.Phone.SetBackgroundColour('red')
            invalid = True
        if invalid:
            return 0 #Cancel saving, mark the missing required fields in red.
        pagingValue = panel.Paging.GetValue()   #(automatically generated)
        try:
            activity = self.activities[panel.Activity.GetSelection()]
        except IndexError:
            activity = None
        medical = panel.Medical.GetValue()
        parent1 = panel.Parent1.GetValue()  #TODO: Add parent linking
        parent2 = panel.Parent2.GetValue()
        email = panel.Email.GetValue()
        notes = panel.Notes.GetValue()
        DOB = panel.DOB.GetValue()
        grade = panel.Grade.GetValue()

        #Check if there's a DOB entered (blank allowed)
        if DOB.lower().encode('ascii') == 'yyyy-mm-dd' or DOB == '':
            DOB = ''               #(true when has focus)——————^
        else: #Validate the entered date.
            a = validate.DateFormat(panel.DOB)
            print a
            if not a:  #date was not validated
                panel.DOB.SetBackgroundColour('orange')
                return 0

        room = panel.Room.GetStringSelection()
        if room == '':  #No room assigned.
            room = None
        if room != None:
            #Convert it to an explicit id reference (I'd use GetSelection(), but the order might be wrong).
            room = self.db.GetRoomID(room)[0]

        if activity['parentTag'] == parentEnable: #Check if the nametag settings have been overridden.
            noParentTag = not(activity['parentTag']) # and set the appropriate value.
        else:
            noParentTag = not(parentEnable)

        #TODO: Reading and setting of mobile carrier setting.
        #TODO: Parent linking

        try:
            panel.Disable()
            ref = self.db.Register(name, surname, phone, parent1, paging=pagingValue,
                mobileCarrier=carrier, activity=activity['id'], room=room, grade=grade,
                parent2=parent2, parentEmail=email, dob=DOB, medical=medical,
                count=0, noParentTag=noParentTag, barcode=None,
                picture=panel.photo, notes=notes)
            self.db.commit()
        except self.database.DatabaseError as e:
            wx.MessageBox('The database was unable to commit this record.\n'
                          'The error was: {0}'.format(e), 'Database Error',
                          wx.OK | wx.ICON_ERROR)
        finally:
            panel.Enable()

        #Save any added barcode values:
        for code in self.BarcodePanel.barcodes:
            if code != '':
                try:
                    panel.Disable()
                    self.db.AddBarcode(ref, code)
                    self.db.commit()
                except self.database.DatabaseError as e:
                    wx.MessageBox('Unable to add barcode value for record {0}.\n'
                                  'The error was: {1}'.format(ref, e),
                                  'Database Error', wx.OK | wx.ICON_ERROR)
                finally:
                    panel.Enable()

        self.BarcodePanel.barcodes = []
        panel.photo = None #Prevent the saved photo from being deleted in CloseRegisterPanel

        self.CloseRegisterPanel(None)

        #Print nametag and do check-in if needed:
        if button == panel.CheckinButton:
            data = { 'id': ref, 'name': name, 'surname': surname,
                     'paging': pagingValue, 'medical': medical,
                     'room': panel.Room.GetStringSelection(),
                     'activity': activity, 'nametag': nametagEnable,
                     'parentTag': parentEnable }
            self.DoCheckin((self.service['name'],), data)

        #Send registration email if needed:
        if activity['registerEmailEnable'] and email != '':
            self.EmailJobID += 1
            delayedresult.startWorker(self._EmailRegisterConsumer,
                self._EmailRegisterProducer,
                wargs=(self.EmailJobID, email, activity['registerEmail']),
                jobID=self.EmailJobID)

    def _EmailRegisterConsumer(self, delayedResult):
        jobID = delayedResult.getJobID()
        assert jobID == self.EmailJobID
        try:
            result = delayedResult.get()
        except Exception, exc:
            notify.error("Thread Error", "Result for job %s raised exception: %s" % (jobID, exc) )
            return

    def _EmailRegisterProducer(self, JobID, recipient, template='default'):
        """
        template: Which template to use ('default')
        section: Which message to send from template ('register')
        recipient: Who to send email to
        """
        import mail
        mail.register(recipient, template)
        return JobID


    def SaveRecord(self, event):
        button = event.GetEventObject()
        panel = button.GetParent()
        nametagEnable = panel.NametagToggle.GetValue()
        parentEnable = panel.ParentToggle.GetValue()
        name = panel.FirstName.GetValue()  #Required
        surname = panel.Surname.GetValue() #Required
        phone = panel.Phone.GetValue()     #Required
        carrier = panel.PhoneCarrier.GetSelection()
        invalid = False
        if name == '':
            panel.FirstName.SetBackgroundColour('red')
            invalid = True
        if surname == '':
            panel.Surname.SetBackgroundColour('red')
            invalid = True
        if phone == '':
            panel.Phone.SetBackgroundColour('red')
            invalid = True
        if invalid:
            return 0 #Cancel saving, mark the missing required fields in red.
        pagingValue = panel.Paging.GetValue()   #(automatically generated)
        activity = self.activities[panel.Activity.GetSelection()]
        medical = panel.Medical.GetValue()
        parent1 = panel.Parent1.GetValue()  #TODO: Add parent linking
        parent2 = panel.Parent2.GetValue()
        email = panel.Email.GetValue()
        notes = panel.Notes.GetValue()
        DOB = panel.DOB.GetValue()
        grade = panel.Grade.GetValue()

        #Check if there's a DOB entered (blank allowed)
        if DOB.lower().encode('ascii') == 'yyyy-mm-dd' or DOB == '':
            DOB = ''               #(true when has focus)——————^
        else: #Validate the entered date.
            a = validate.DateFormat(panel.DOB)
            if not a:  #date was not validated
                panel.DOB.SetBackgroundColour('orange')
                return 0

        room = panel.Room.GetStringSelection()
        if room == '':  #No room assigned.
            room = None
        if room != None:
            #Convert it to an explicit id reference (I'd use GetSelection(), but the order might be wrong).
            room = self.db.GetRoomID(room)[0]

        if activity['parentTag'] == parentEnable: #Check if the nametag settings have been overridden.
            noParentTag = not(activity['parentTag']) # and set the appropriate value.
        else:
            noParentTag = not(parentEnable)

        #TODO: Reading and setting of mobile carrier setting.
        #TODO: Parent linking
        index = self.RecordPanel.data['id']
        try:
            self.db.Update(index, name, surname, phone, parent1, paging=pagingValue,
                mobileCarrier=carrier, activity=activity['id'], room=room, grade=grade,
                parent2=parent2, parentEmail=email, dob=DOB, medical=medical,
                count=0, noParentTag=noParentTag, barcode=None,
                picture=panel.data['picture'], notes=notes,
                joinDate=panel.data['joinDate'], 
                lastSeen=panel.data['lastSeen'])
            self.db.commit()
        except self.database.DatabaseError as e:
            wx.MessageBox('The database was unable to commit this record.\n'
                          'The error was: {0}'.format(e), 'Database Error',
                          wx.OK | wx.ICON_ERROR)
        except Error as e:
            wx.MessageBox('The database was unable to commit this record.\n'
                          'The error was: {0}'.format(e), 'Database Error',
                          wx.OK | wx.ICON_ERROR)

        #Reset and save any barcode values:
        try:
            self.db.RemoveAllBarcodes(self.RecordPanel.data['id'])
            self.db.commit()
        except self.database.DatabaseError:
            pass
        for code in self.BarcodePanel.barcodes:
            if code != '':
                try:
                    self.db.AddBarcode(index, code)
                    self.db.commit()
                except self.database.DatabaseError as e:
                    wx.MessageBox('Unable to add barcode value for record {0}.\n'
                                  'The error was: {1}'.format(ref, e),
                                  'Database Error', wx.OK | wx.ICON_ERROR)

        self.BarcodePanel.barcodes = []
        panel.photo = None #Prevent the saved photo from being deleted later

        if button == panel.CheckinButton:  #Don't close the panel yet, call checkin/printing thread:
            data = { 'id': index, 'name': name, 'surname': surname,
                     'paging': pagingValue, 'medical': medical,
                     'room': panel.Room.GetStringSelection(),
                     'activity': activity, 'nametag': nametagEnable,
                     'parentTag': parentEnable }
            self.DoCheckin((self.service['name'],), data)
            
        if button == panel.MultiServiceButton:
            #Prompt the user for services selection:
            self.services = self.db.GetServices()
            dlg = SearchResultsList.MultiServiceDialog(self.frame, wx.ID_ANY, self.services)
            if dlg.ShowModal() == wx.ID_OK:
                print "DEBUG"
                print dlg.selected
                print [ i ['name'] for i in dlg.selected ]
                if dlg.selected != []: #Make sure something's selected
                    services = [ i['name'] for i in dlg.selected ]
                    data = { 'id': index, 'name': name, 'surname': surname,
                         'paging': pagingValue, 'medical': medical,
                         'room': panel.Room.GetStringSelection(),
                         'activity': activity, 'nametag': nametagEnable,
                         'parentTag': parentEnable }
                    self.DoCheckin(services, data)
                else:
                    notify.info("Checkin incomplete", "No services selected.")
                    dlg.Destroy()
                    return
            else:
                dlg.Destroy()
                return
            dlg.Destroy()
            
        self.CloseRecordPanel(None)
        if self.ResultsPanel.opened:
            #Reload the query:
            self.OnSearch(None)
    
    def OnMultiCheckin(self, event):
        checked = self.ResultsList.GetSelected() #Index of checked items
        
        #Remove those already marked as checked-in.
        for i in checked:
            if self.ResultsList.results[i]['status'] == taxidi.STATUS_CHECKED_IN:
                checked.remove(i)
            else:
                self.ResultsList.results[i]['status'] = taxidi.STATUS_CHECKED_IN
                self.ResultsList.UpdateStatus(i)
        
        #Convert them to explicit database id references
        selected = [ self.ResultsList.results[i]['id'] for i in checked ]
        
        #Convert references into full data dictionary useable by check-in producer
        fullResults =  []
        for row in self.results:
            for i in selected:
                if i == row['id']:
                    fullResults.append(row)
                    
        #Perform check-in on database and printing.
        self.DoMultiCheckin((self.service['name'],), fullResults)
        
        #Close the result panel:
        self.CloseResults(None)
        
    def OnMultiCheckinMultiService(self, event):
        #^ This needs a better method name
        
        #Get the selected items.
        checked = self.ResultsList.GetSelected() #Index of checked items
        
        #Remove those already marked as checked-in.
        for i in checked:
            if self.ResultsList.results[i]['status'] == taxidi.STATUS_CHECKED_IN:
                checked.remove(i)
            else:
                self.ResultsList.results[i]['status'] = taxidi.STATUS_CHECKED_IN
                self.ResultsList.UpdateStatus(i)
                
        #Stop if nothing's selected:
        if len(checked) == 0:
            return
        
        #Convert them to explicit database id references
        selected = [ self.ResultsList.results[i]['id'] for i in checked ]
        
        #Convert references into full data dictionary useable by check-in producer
        fullResults =  []
        for row in self.results:
            for i in selected:
                if i == row['id']:
                    fullResults.append(row)
        
        #Prompt the user for services selection:
        self.services = self.db.GetServices()
        dlg = SearchResultsList.MultiServiceDialog(self.frame, wx.ID_ANY, self.services)
        if dlg.ShowModal() == wx.ID_OK:
            if dlg.selected != []: #Make sure something's selected
                #Selected services as list for use by check-in producer
                services = [ i['name'] for i in dlg.selected ]
                print "services ", services
                
                #Perform check-in on database and printing.
                self.DoMultiCheckin(services, fullResults)
            else:
                notify.info("Checkin incomplete", "No services selected.")
                dlg.Destroy()
                return
        else:
            dlg.Destroy()
            return
        dlg.Destroy()
        
        #Close the result panel:
        self.CloseResults(None)
            
    def DoMultiCheckin(self, services, data):
        self.multiJobID += 1
        delayedresult.startWorker(self._multiCheckinConsumer, self._multiCheckinProducer,
                                  wargs=(self.multiJobID, data, services),
                                  jobID=self.multiJobID)
        time.sleep(0.6)
        return 0
        
    def _multiCheckinConsumer(self, delayedResult):
        jobID = delayedResult.getJobID()
        assert jobID == self.multiJobID
        try:
            result = delayedResult.get()
        except Exception, exc:
            notify.error("Thread Error", "Result for job %s raised exception: %s" % (jobID, exc) )
            raise
            return
        
    def _multiCheckinProducer(self, jobID, data, services):
        #Note: activity is a dictionary
        #Note: dictionary keys match database, not _checkinProducer()
        #Get secure code, if needed
        self.activities = self.db.GetActivities()
        trash = []
        for row in data:
            print row['activity']
            activity = self.activities[row['activity']-1]
            room = self.db.GetRoomByID(row['room'])
            
            if activity['securityTag']:
                if conf.as_bool(conf.config['config']['secureCodeRemote']):
                    #Use remote
                    code_generator = taxidi.SecureCode(conf.config['config']['secureCodeURI'])
                else:
                    code_generator = taxidi.SecureCode() #Use local generator
                secure = code_generator.request() #Draw a code
                del code_generator #TODO: put generator initialization in BeginCheckinRoutine
    
                #Hash secure mode if needed
                if activity['securityMode'].lower() == 'simple':
                    parentSecure = secure
                elif activity['securityMode'].lower() == 'md5':
                    parentSecure = secure
                    import hashlib
                    secure = hashlib.md5(secure).hexdigest()[:4].upper()
            else:
                secure = None
                parentSecure = None
    
            #Check-in user into the database, using a new cursor to keep
            #  the program thread-safe.
            if activity['autoExpire']:
                expires = self.services[-1]['endTime']
            else:
                expires = None
            location = conf.config['config']['name']
            try:
                #~ cursor = self.db.spawnCursor()
                self.db.DoCheckin(row['id'], services, expires, secure,
                    location, activity['name'], room)
                self.db.commit()
            except self.database.DatabaseError as e:
                notify.error("Database Error", "A database error occurred " \
                    "while trying to check-in {0}.  Please check the database "\
                    "connection (Check-in was aborted).".format(data['name']))
                raise
                
            #Do printing
            if activity['nametagEnable'] == True:
                if secure == None:
                    barcode = False
                else:
                    barcode = True
                #Generate the nametag:
                self.printing.nametag(theme=activity['nametag'], room=room,
                                      first=row['name'], last=row['lastname'],
                                      medical=row['medical'], code=row['paging'],
                                      secure=secure, barcode=barcode)
                if conf.as_bool(conf.config['printing']['preview']):
                    #Open print preview
                    self.printing.preview()
                    trash.append(self.printing.pdf) #Delete it later
                if conf.as_bool(conf.config['printing']['enable']):
                    if conf.config['printing']['printer'] == '':
                        self.printing.printout() #Use default printer
                    else:
                        #TODO: do validation against printer name.
                        self.printing.printout(printer=conf.config['printing']['printer'])
    
    
            if activity['parentTagEnable']: #Print parent tag if needed:
                if secure != None:
                    barcode = False
                else:
                    barcode = True
                link = activity['parentURI']
                self.printing.parent(theme=activity['nametag'], room=room,
                                     first=row['name'], last=row['lastname'],
                                     code=row['paging'], secure=parentSecure,
                                     link=link)
                if conf.as_bool(conf.config['printing']['preview']):
                    #Open preview
                    self.printing.preview()
                    trash.append(self.printing.pdf)
                #Do printing if needed
                if conf.as_bool(conf.config['printing']['enable']):
                    if conf.config['printing']['printer'] == '':
                        self.printing.printout() #Use default printer
                    else:
                        #TODO: do validation against printer name.
                        self.printing.printout(printer=conf.config['printing']['printer'])

        wx.CallLater(5000, self.printing.cleanup, trash) #Delete temporary files later
                
        return jobID
    
    def DoCheckin(self, services, data, printOnly=False):
        """
        This method is for checking in one person.
        'data' is a dictionary containing the following keys: 'id', 'name',
        'surname', 'paging', 'medical', 'room', 'activity', 'nametag', 'parentTag'.
        """
        #(Create fork, perform check-in)
        #~ self._checkinProducer(0, data, services, data['activity'], data['room'])
        self.jobID += 1
        delayedresult.startWorker(self._checkinConsumer, self._checkinProducer,
                                  wargs=(self.jobID, data, services,
                                         data['activity'], data['room'], printOnly),
                                  jobID=self.jobID)
        time.sleep(0.6)  #Give the database time to settle (sqlite3 thread-safe?)
        return 0

    def _checkinProducer(self, jobID, data, services, activity, room, printOnly=False):
        #Note: activity is a dictionary
        #Get secure code, if needed
        if activity['securityTag']:
            if conf.as_bool(conf.config['config']['secureCodeRemote']):
                #Use remote
                code_generator = taxidi.SecureCode(conf.config['config']['secureCodeURI'])
            else:
                code_generator = taxidi.SecureCode() #Use local generator
            secure = code_generator.request() #Draw a code
            del code_generator #TODO: put generator initialization in BeginCheckinRoutine

            #Hash secure mode if needed
            if activity['securityMode'].lower() == 'simple':
                parentSecure = secure
            elif activity['securityMode'].lower() == 'md5':
                parentSecure = secure
                import hashlib
                secure = hashlib.md5(secure).hexdigest()[:4].upper()
        else:
            secure = None
            parentSecure = None

        #Check-in user into the database, using a new cursor to keep
        #  the program thread-safe.
        if activity['autoExpire']:
            expires = self.services[-1]['endTime']
        else:
            expires = None
        location = conf.config['config']['name']
        if not printOnly:
            try:
                #~ cursor = self.db.spawnCursor()
                self.db.DoCheckin(data['id'], services, expires, secure,
                    location, activity['name'], room)
                self.db.commit()
            except self.database.DatabaseError as e:
                notify.error("Database Error", "A database error occurred " \
                    "while trying to check-in {0}.  Please check the database "\
                    "connection (Check-in was aborted).".format(data['name']))
                raise

        #Do printing
        trash = []
        if data['nametag'] == True:
            if secure == None:
                barcode = False
            else:
                barcode = True
            #Generate the nametag:
            self.printing.nametag(theme=activity['nametag'], room=room,
                                  first=data['name'], last=data['surname'],
                                  medical=data['medical'], code=data['paging'],
                                  secure=secure, barcode=barcode)
            if conf.as_bool(conf.config['printing']['preview']):
                #Open print preview
                self.printing.preview()
                trash.append(self.printing.pdf) #Delete it later
            if conf.as_bool(conf.config['printing']['enable']):
                if conf.config['printing']['printer'] == '':
                    self.printing.printout() #Use default printer
                else:
                    #TODO: do validation against printer name.
                    self.printing.printout(printer=conf.config['printing']['printer'])


        if data['parentTag']: #Print parent tag if needed:
            if secure != None:
                barcode = False
            else:
                barcode = True
            link = activity['parentURI']
            self.printing.parent(theme=activity['nametag'], room=room,
                                 first=data['name'], last=data['surname'],
                                 code=data['paging'], secure=parentSecure,
                                 link=link)
            if conf.as_bool(conf.config['printing']['preview']):
                #Open preview
                self.printing.preview()
                trash.append(self.printing.pdf)
            #Do printing if needed
            if conf.as_bool(conf.config['printing']['enable']):
                if conf.config['printing']['printer'] == '':
                    self.printing.printout() #Use default printer
                else:
                    #TODO: do validation against printer name.
                    self.printing.printout(printer=conf.config['printing']['printer'])

        wx.CallLater(1000, self.printing.cleanup, trash) #Delete temporary files later
        return jobID

    def _checkinConsumer(self, delayedResult):
        jobID = delayedResult.getJobID()
        assert jobID == self.jobID
        try:
            result = delayedResult.get()
        except Exception, exc:
            notify.error("Thread Error", "Result for job %s raised exception: %s" % (jobID, exc))
            self.log.error("Thread Error: Result for job %s raised exception: %s" % (jobID, exc))
            print traceback.format_exc()
            self.log.error(traceback.format_exc())
            return
            
    def UpdateStatusCheckedOut(self, i):
        self.ResultsList.results[i]['status'] = taxidi.STATUS_CHECKED_OUT
        self.ResultsList.results[i]['checkout-time'] = datetime.now().strftime("%H:%M:%S")
        self.ResultsList.UpdateStatus(i)

    def OnListCheckout(self, event):
        #Do checkout
        #FIXME: change calling even back to green check if checkout is cancelled or fails
        data = event.data
        ctrl = event.GetEventObject()
        self.activities = self.db.GetActivities()
        for act in self.activities:
            if data['activity'] == act['name']:
                activity = act
    
        status = self.db.GetStatus(data['id'], True)
        code = status['code']
          
        if activity['securityMode'].lower() == 'simple':
            parent = self.parentPrompt()
            if parent == None:
                self.ToggleCheckBoxOn(ctrl)
                return

            if code.lower() == parent.lower():
                self.DoCheckout(data, hold=True)
                self.UpdateStatusCheckedOut(ctrl.id) 
            else:
                wx.MessageBox('The security code was incorrect.', 'Taxidi',
                        wx.OK | wx.ICON_ERROR)
                self.ToggleCheckBoxOn(ctrl)

        elif activity['securityMode'].lower() == 'md5':
            parent = self.parentPrompt()
            if parent == None:
                self.ToggleCheckBoxOn(ctrl)
                return

            if hashlib.md5(parent).hexdigest()[:4] == code.lower():
                self.DoCheckout(data, hold=True)
                self.UpdateStatusCheckedOut(ctrl.id) 
            else: 
                wx.MessageBox('The security code was incorrect.', 'Taxidi',
                        wx.OK | wx.ICON_ERROR)
                self.ToggleCheckBoxOn(ctrl)
            
        else:
            self.DoCheckout(data, hold=True)
            #Update the status column to reflect checkout time
            self.UpdateStatusCheckedOut(ctrl.id) 


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

        #Bind list clicking:
        self.ResultsList.ultimateList.Bind(wx.EVT_LIST_ITEM_SELECTED, self.SelectResultItem)
        #Bind check-box clicking:
        self.ResultsList.Bind(SearchResultsList.RESULT_LIST_CHECK, self.CheckResultItem)
        #Bind check-out action:
        self.ResultsList.Bind(SearchResultsList.EVT_CHECKOUT, self.OnListCheckout)

        #Perform initial resizes.
        self.ResultsList.SetSize((1024, 407))
        self.ResultsPanel.SetSize((1024, 540))
        self.ResultsPanel.SetPosition((0, 160))
        self.ResultsPanel.CentreOnParent(dir=wx.HORIZONTAL)

        self.ResultsControls = wx.Panel(self.ResultsPanel,-1)
        self.ResultsControls.SetBackgroundColour(themeBackgroundColour)

        #Create buttons for the top control panel
        self.ResultsControls.Photo = wx.BitmapButton(self.ResultsControls, -1,
            wx.Bitmap('resources/icons/no-photo-100.png'), size=(100, 100))
        self.ResultsControls.Close = wx.BitmapButton(self.ResultsControls, -1,
            wx.Bitmap('resources/icons/window-close.png'), size=(150, 50))
        self.ResultsControls.CheckIn = wx.Button(self.ResultsControls, -1,
            'Check-in', size=(150, 50))
        self.ResultsControls.CheckIn.SetDefault()
        self.ResultsControls.Display = wx.Button(self.ResultsControls, -1,
            'Display', size=(150, 50))
        self.ResultsControls.MultiService = wx.Button(self.ResultsControls, -1,
            'Multi-Service', size=(150, 50))
        #Group some of the buttons together:
        buttonSizer = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        buttonSizer.Add(self.ResultsControls.CheckIn, -1)
        buttonSizer.Add(self.ResultsControls.Close, -1)
        buttonSizer.Add(self.ResultsControls.MultiService, -1)
        buttonSizer.Add(self.ResultsControls.Display, -1, wx.RIGHT, border=10)

        #Disable actions when nothing's selected
        self.ResultsControls.CheckIn.Disable()
        self.ResultsControls.Display.Disable()
        self.ResultsControls.MultiService.Disable()

        #Bind some buttons:
        self.ResultsControls.Photo.Bind(wx.EVT_BUTTON, self.ShowPhotoPanel)
        self.ResultsControls.Close.Bind(wx.EVT_BUTTON, self.CloseResults)
        self.ResultsControls.Display.Bind(wx.EVT_BUTTON, self.DisplaySelectedRecord)
        self.ResultsControls.CheckIn.Bind(wx.EVT_BUTTON, self.OnMultiCheckin)
        self.ResultsControls.MultiService.Bind(wx.EVT_BUTTON, self.OnMultiCheckinMultiService)

        #Create statictexts:
        self.ResultsControls.Text = wx.StaticText(self.ResultsControls,
            label='Results for ????')
        self.ResultsControls.Text.SetForegroundColour(themeTextColour)
        font = wx.Font(22, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.ResultsControls.Text.SetFont(font)
        searchInstructions = wx.StaticText(self.ResultsControls,
            label = 'Check one or more records and select an action.\n'
            'To edit or view detals, highlight a record and click "Display".')
        searchInstructions.SetForegroundColour(themeTextColour)
        #And put them in a sizer.
        textBox = wx.FlexGridSizer(rows=2, cols=1, vgap=10, hgap=10)
        textBox.Add(self.ResultsControls.Text, -1)
        textBox.Add(searchInstructions, -1)

        #The master sizer for the whole shebang:
        listSizer = wx.BoxSizer(wx.VERTICAL)
        listSizer.Add(self.ResultsControls, 1, wx.EXPAND)
        listSizer.Add(self.ResultsList, 4, wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)

        #Top-level sizer for ResultsControls panel
        controlsSizer = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        controlsSizer.Add(self.ResultsControls.Photo, -1,
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
        self.ResultsPanel.opened = False
        self.ResultsPanel.Text = self.ResultsControls.Text
        self.ResultsList.selected = None

    def SelectResultItem(self, event):
        selected = event.m_itemIndex
        self.ResultsList.selected = event.m_itemIndex #Remember the selection
        self.ResultsControls.Display.Enable()
        try: #Display the record's picture:
            self.ResultsControls.Photo.SetBitmapLabel(
                self.PhotoStorage.getThumbnail100(
                self.ResultsList.results[selected]['picture']))
        except:
            self.ResultsControls.Photo.SetBitmapLabel(self.NoPhoto100)

    def CheckResultItem(self, event):
        if len(self.ResultsList.GetSelected()) == 0:
            self.ResultsControls.CheckIn.Disable()
            self.ResultsControls.MultiService.Disable()
        else:
            self.ResultsControls.CheckIn.Enable()
            self.ResultsControls.MultiService.Enable()

    def DisplaySelectedRecord(self, event):
        ref = self.ResultsList.results[self.ResultsList.selected]['id']
        details = self.db.GetRecordByID(ref)
        self.ShowRecordPanel()
        self.SetRecordData(details)

    def ShowRecordPanel(self):
        self.HideAll()
        if self.user['leftHanded']:
            self.RecordPanel = self.RecordPanelLeft
        else:
            self.RecordPanel = self.RecordPanelRight
        self.RecordPanel.Show()

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
        panels = (self.VisitorPanelRight, self.VisitorPanelLeft)
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
            
            pane.MultiServiceButton.Disable()
            pane.AddSibling.Disable()

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
            pane.FirstName = xrc.XRCCTRL(pane, 'Name')
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
        carrier = self.VisitorPanel.PhoneCarrier.GetSelection()
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

        #Attempt to add record to database:
        try:
            ref = self.db.Register(name, surname, phone, parent, paging=paging,
                mobileCarrier=0, activity=activity['id'], room=room,
                parentEmail=email, medical=medical, visitor=True,
                expiry=expiration, noParentTag=noParentTag, barcode=None,
                picture=self.VisitorPanel.photo,
                authorized=None, unauthorized=None, notes='')
            self.db.commit() #Commit the change
        except self.database.DatabaseError as e:
            if e.code == self.database.EMPTY_RESULT:
                wx.MessageBox('The record was unable to be added to the database.',
                              'Taxidi Database Error', wx.OK | wx.ICON_ERROR)

            return 0  #Don't close the panel

        #Do printing if needed: (And checkin!)
        activity = self.activities[self.VisitorPanel.Activity.GetSelection()]
        data = {'id': ref, 'name': name, 'surname': surname, 
                'paging': paging, 'medical': medical, 
                'activity': activity, 
                'room': self.VisitorPanel.Room.GetStringSelection(),
                'nametag': nametagEnable, 'parentTag': parentEnable }
        self.DoCheckin((self.service['name'],), data)

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

    def RegisterPhoto(self, event):
        if conf.as_bool(conf.config['webcam']['enable']): #Webcam enabled?
            #Hide the register panel
            self.HideAll()
            if self.RegisterPanel.photo != None:
                #re-take; overwrite the old photo.
                self.WebcamPanel.SetOverwrite(self.RegisterPanel.photo)
            #Show the webcam input panel.
            self.ShowWebcamPanel(self.RegisterPhotoCancel, \
                self.RegisterPhotoSave, self.RegisterPhotoFile)
        else:
            #Just open a file selection dialog.
            path = os.path.abspath(os.path.expanduser(
                conf.config['webcam']['target']))
            dlg = ib.ImageDialog(self.frame, path)
            dlg.Centre()
            if dlg.ShowModal() == wx.ID_OK:
                if self.RegisterPanel.photo != None:
                    self.RegisterPanel.photo = \
                        self.PhotoStorage.saveImage(dlg.GetFile(),
                        int(self.RegisterPanel.photo))
                else:
                    self.RegisterPanel.photo = self.PhotoStorage.saveImage(dlg.GetFile())

                photoPath = self.PhotoStorage.getThumbnailPath(self.RegisterPanel.photo)
                #~ print "Resolves to file: {0}".format(photoPath)
                #Load and display new photo
                wximg = wx.Image(photoPath)
                wxbmp = wximg.ConvertToBitmap()
                self.RegisterPanel.ProfilePicture.SetBitmapLabel(wxbmp)

            else:
                #~ self.log.debug("> Dialogue cancelled.")
                pass

            dlg.Destroy()

    def RecordPhoto(self, event):
        """
        Takes a picture from webcam or file selection and updates the record's
        photo.  Works on calling panel's `data` dictionary attribute
        (self.RecordPanel.data['picture'], usw.)

        Sets the panel's BitmapButton `ProfilePicture` attribute to the new picture.
        """
        event.GetEventObject().GetParent().Hide() #Hide the calling panel
        panel = event.GetEventObject().GetParent().ParentObject
        if conf.as_bool(conf.config['webcam']['enable']): #Webcam enabled?
            #Save the original calling panel:
            self.WebcamPanel.ParentObject = panel
            panel.Hide() #Hide it for now
            if panel.data['picture'] != None:
                #re-take; overwrite the old photo.
                if panel.data['picture'] == '':
                    panel.data['picture'] = None
                try:
                    f = open(self.PhotoStorage.getImagePath(panel.data['picture']))
                    f.close()
                    self.WebcamPanel.SetOverwrite(panel.data['picture'])
                except:
                    self.WebcamPanel.SetOverwrite(None)
            #Show the webcam input panel, setting call-back functions:
            self.ShowWebcamPanel(self.PanelPhotoCancel, \
                self.PanelPhotoSave, self.PanelPhotoFile)
            self.WebcamPanel.ParentObject = panel
        else:
            #Just open a file selection dialog.
            path = os.path.abspath(os.path.expanduser(
                conf.config['webcam']['target']))
            dlg = ib.ImageDialog(self.frame, path)
            dlg.Centre()
            if dlg.ShowModal() == wx.ID_OK:
                if panel.data['picture'] != None:
                    panel.data['picture'] = \
                        self.PhotoStorage.saveImage(dlg.GetFile(),
                        int(panel.data['picture']))
                else:
                    panel.data['picture'] = self.PhotoStorage.saveImage(dlg.GetFile())

                photoPath = self.PhotoStorage.getThumbnailPath(self.RegisterPanel.photo)
                #~ print "Resolves to file: {0}".format(photoPath)
                #Load and display new photo
                wximg = wx.Image(photoPath)
                wxbmp = wximg.ConvertToBitmap()
                panel.ProfilePicture.SetBitmapLabel(wxbmp)
                panel.Show()

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

    def RegisterPhotoFile(self, event):
        self.ShowRegisterPanel()
        self.CloseWebcamPanel()
        photo = self.WebcamPanel.GetFile()
        if self.RegisterPanel.photo != None:
            self.RegisterPanel.photo = self.PhotoStorage.saveImage(photo, \
                int(self.RegisterPanel.photo))
        else:
            self.RegisterPanel.photo = self.PhotoStorage.saveImage(photo)

        photoPath = self.PhotoStorage.getThumbnailPath(self.RegisterPanel.photo)
        print "Resolves to file: {0}".format(photoPath)
        #Load and display new photo
        wximg = wx.Image(photoPath)
        wxbmp = wximg.ConvertToBitmap()
        self.RegisterPanel.ProfilePicture.SetBitmapLabel(wxbmp)

    def PanelPhotoFile(self, event):
        self.WebcamPanel.ParentObject.Show()
        self.CloseWebcamPanel()
        photo = self.WebcamPanel.GetFile()
        if self.WebcamPanel.ParentObject.data['picture'] != None:
            self.WebcamPanel.ParentObject.data['picture'] = self.PhotoStorage.saveImage(photo, \
                int(self.WebcamPanel.ParentObject.data['picture']))
        else:
            self.WebcamPanel.ParentObject.data['picture'] = self.PhotoStorage.saveImage(photo)

        photoPath = self.PhotoStorage.getThumbnailPath(self.WebcamPanel.ParentObject.data['picture'])
        print "Resolves to file: {0}".format(photoPath)
        #Load and display new photo
        wximg = wx.Image(photoPath)
        wxbmp = wximg.ConvertToBitmap()
        self.WebcamPanel.ParentObject.ProfilePicture.SetBitmapLabel(wxbmp)

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

    def RegisterPhotoSave(self, evt):
        photo = self.WebcamPanel.GetFile()
        print "Got photo ID: {0}".format(photo)
        self.RegisterPanel.photo = photo
        photoPath = self.PhotoStorage.getThumbnailPath(photo)
        print "Resolves to file: {0}".format(photoPath)
        self.ShowRegisterPanel()
        #Load and display new photo
        wximg = wx.Image(photoPath)
        wxbmp = wximg.ConvertToBitmap()
        self.RegisterPanel.ProfilePicture.SetBitmapLabel(wxbmp)
        self.CloseWebcamPanel()

    def PanelPhotoSave(self, evt):
        photo = self.WebcamPanel.GetFile()
        print "Panel Photo Save function"
        print "Got photo ID: {0}".format(photo)
        self.WebcamPanel.ParentObject.data['picture'] = photo
        photoPath = self.PhotoStorage.getThumbnailPath(photo)
        print "Resolves to file: {0}".format(photoPath)
        #Show the original panel:
        self.WebcamPanel.ParentObject.Show()
        #Load and display new photo
        wximg = wx.Image(photoPath)
        wxbmp = wximg.ConvertToBitmap()
        self.WebcamPanel.ParentObject.ProfilePicture.SetBitmapLabel(wxbmp)
        self.WebcamPanel.ParentObject.data['picture'] = photo
        self.WebcamPanel.ParentObject.photo = photo
        self.CloseWebcamPanel()

    def VisitorPhotoCancel(self, evt):
        self.ShowVisitorPanel()
        self.CloseWebcamPanel()

    def PanelPhotoCancel(self, evt):
        self.WebcamPanel.ParentObject.Show()
        self.CloseWebcamPanel()

    def RegisterPhotoCancel(self, evt):
        self.ShowRecordPanel()
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

    def FormatParentPhoneLive(self, event):
        phone = event.GetEventObject()
        if phone.IsModified():
            validate.PhoneFormat(phone)

    def FormatDateLive(self, event):
        dob = event.GetEventObject()
        if dob.IsModified():
             if validate.DateFormat(dob):
                 self.RecordPanel.AgeText.SetLabel(str(
                    calculate_age(
                    date(*(
                    time.strptime(dob.GetValue(), '%Y-%m-%d')[0:3]
                    )))))


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

    def OnRegister(self, event):
        #Setup the inputs, etc.
        self.activities = self.db.GetActivities() #Load activities from database
        self.ShowRegisterPanel() #Show panel (sets self.RegisterPanel to the appropriate value.)
        #Set activity options:
        self.RegisterPanel.Activity.SetItems([ i['name'] for i in self.activities ])
        self.RegisterPanel.Activity.SetStringSelection(
            conf.config['config']['defaultActivity']) #Set default activity
        #Set nametag printing toggles:
        activities = dict( (i['name'], i['nametagEnable']) for i in self.activities )
        if activities[conf.config['config']['defaultActivity']]:
            self.ToggleStateOn(self.RegisterPanel.NametagToggle)
        else:
            self.ToggleStateOff(self.RegisterPanel.NametagToggle)
        activities = dict( (i['name'], i['parentTagEnable']) for i in self.activities )
        if activities[conf.config['config']['defaultActivity']]:
            self.ToggleStateOn(self.RegisterPanel.ParentToggle)
        else:
            self.ToggleStateOff(self.RegisterPanel.ParentToggle)

        self.rooms = self.db.GetRooms()
        items = [ i['name'] for i in self.db.GetRoom(
            conf.config['config']['defaultActivity']) ]
        items.insert(0, '') #Allow blank selection
        self.RegisterPanel.Room.SetItems(items)
        self.RegisterPanel.Room.SetStringSelection('')
        #Set focus to the first field:
        self.RegisterPanel.FirstName.SetFocus()

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
        if panel == self.VisitorPanelLeft or panel == self.VisitorPanelRight:
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
        if query == '':
            self.Search.SetBackgroundColour('pink')
            self.Search.SetFocus()
            return 0
        #TODO: Respect advanced search selection
        results = self.db.Search(query)
        if len(results) == 1:
            #Show single record
            self.ShowRecordPanel()
            self.SetRecordData(results[0])
        elif len(results) > 1:
            #Multiple results:
            self.ShowResultsPanel()
            self.ResultsControls.Text.SetLabel('Results for “{0}”'.format(query))
            self.ResultsControls.CheckIn.Disable()  #Disable actions (nothing's selected)
            self.ResultsControls.Display.Disable()
            self.ResultsControls.MultiService.Disable()
            self.results = results #Remember original query results
            self.ResultsList.results = self.FormatResults(results)
            self.ResultsList.ShowResults(self.ResultsList.results)

            #Display picture of first record
            try:
                self.ResultsControls.Photo.SetBitmapLabel(
                    self.PhotoStorage.getThumbnail100(
                    self.ResultsList.results[0]['picture']))
            except:
                self.ResultsControls.Photo.SetBitmapLabel(self.NoPhoto100)
        else: #No results
            self.Search.SetBackgroundColour('pink')
            notify.warning("No results", 'No results for "{0}".'.format(query))
            self.Search.SetFocus()
            return 0
        self.SearchPanel.SearchAny.SetValue(True) #Reset advanced search choice

        #~ if query == '2244':
            #~ #Throw up some test data:
            #~ self.ShowResultsPanel()
            #~ results = [ {'name':'Johnathan Churchgoer', 'activity':'Explorers',  'room':'Jungle Room', 'status':taxidi.STATUS_NONE},
                    #~ {'name':'Jane Smith',           'activity':'Explorers',  'room':'Ocean Room',  'status':taxidi.STATUS_CHECKED_IN},
                    #~ {'name':'Joseph Flint',         'activity':'Outfitters', 'room':u'—',          'status':taxidi.STATUS_CHECKED_OUT, 'checkout-time':'11:46:34'} ]
            #~ self.ResultsList.ShowResults(results)
        #~ elif query == '9989':
            #~ #Show single result:
            #~ self.ShowRecordPanel()
        #~ else:  #Bad query
            #~ self.Search.SetBackgroundColour('red')
            #~ self.Search.SetFocus()

    def OnCheckOut(self, event):
        data = self.RecordPanel.data
        if self.activities[data['activity']-1]['securityMode'].lower() == 'simple':
            parent = self.parentPrompt()
            if parent == None:
                return
            code = self.db.GetStatus(data['id'], True)['code']

            print (code, parent)
            if code.lower() == parent.lower():
                self.DoCheckout(data)
            else:
                wx.MessageBox('The security code was incorrect.', 'Taxidi',
                        wx.OK | wx.ICON_ERROR)

        elif self.activities[data['activity']-1]['securityMode'].lower() == 'md5':
            parent = self.parentPrompt()
            code = self.db.GetStatus(data['id'], True)['code']

            if hashlib.md5(parent).hexdigest()[:4] == code.lower():
                self.DoCheckout(data)
            else: 
                wx.MessageBox('The security code was incorrect.', 'Taxidi',
                        wx.OK | wx.ICON_ERROR)
        else:
            self.DoCheckout()
            
    def DoCheckout(self, data, hold=False): #hold=True will not close the panel when done.
        self.db.DoCheckout(data['id'])
        self.db.commit()
        if hold == False:
            self.HideAll()
            self.ShowSearchPanel()
        notify.info("Taxidi", "Checked out {0} successfully.".format(data['name']))
        

    def parentPrompt(self):
        #TODO: make this big and prettier
        dlg = wx.TextEntryDialog(
                self.frame, 'Please scan or key in the parent portion of the\n'
                'security code to complete check-out.',
                'Security Check-out Code')
        if dlg.ShowModal() == wx.ID_OK:
            parent = dlg.GetValue()
        else:
            parent = None
        dlg.Destroy()
        return parent


    def FormatResults(self, results):
        """
        Formats a results dictionary for displaying on the results panel.
        Joins with activity name, room name, and check-in status.
        """
        ret = []
        activities = [ activity['name'] for activity in self.db.GetActivities() ]
        #~ rooms = { i['id'] : i['name'] for i in self.db.GetRooms() }
        #Fixed for python 2.6. (Dict comprehensions only >= 2.7)
        rooms = dict( (room['id'], room['name']) for room in self.db.GetRooms() )
        for record in results:
            room = ''
            if record['room'] != None:
                if int(record['room']) > len(rooms): #Room reference is invalid:
                    record['room'] = 0
            if record['room'] == None or record['room'] == 0:
                room = u'—'
            else:
                room = rooms[int(record['room'])]
            if int(record['activity'])-1 > len(activities): #activity/room index starts at 0
                record['activity'] = 0
            #Get status:
            status = self.db.GetStatus(record['id'], True)
            if status['status'] == taxidi.STATUS_CHECKED_OUT:
                checkout = status['checkout']
            else:
                checkout = None

            ret.append({ 'id': record['id'], 'name': ('%s %s' % (record['name'], record['lastname'])),
                         'activity': activities[int(record['activity'])-1],
                         'room': room, 'status': status['status'],
                         'checkout-time': checkout, 'code': status['code'],
                         'picture': str(record['picture']) })
        return ret

    def SetRecordData(self, data):
        """
        Sets the data for RecordPanel from a search result dictionary.
        Also sets the available Activity and Room selections.
        Be sure to call ShowRecordPanel() first.
        """
        #Remember what was loaded:
        self.RecordPanel.data = data
        #Setup the inputs, etc.
        self.activities = self.db.GetActivities() #Load activities from database
        #Set activity options:
        self.RecordPanel.Activity.SetItems([ i['name'] for i in self.activities ])
        self.RecordPanel.Activity.SetStringSelection(
            conf.config['config']['defaultActivity']) #Set default activity
        self.rooms = self.db.GetRooms()
        items = [ i['name'] for i in self.db.GetRoom(
            conf.config['config']['defaultActivity']) ]
        items.insert(0, '') #Allow blank selection
        self.RecordPanel.Room.SetItems(items)
        panel = self.RecordPanel
        panel.NameText.SetLabel(data['name'])
        panel.FirstName.SetValue(data['name'])
        panel.SurnameText.SetLabel(data['lastname'])
        panel.Surname.SetValue(data['lastname'])
        if data['visitor']:
            panel.StatusText.SetLabel('Visitor')
        else:
            panel.StatusText.SetLabel('Member')
        if data['grade'] == None: data['grade'] = ''
        panel.Grade.SetValue(str(data['grade']))
        panel.Phone.SetValue(str(data['phone']))
        validate.PhoneFormat(panel.Phone) #Format the number if needed.
        try:
            panel.PhoneCarrier.SetSelection(int(data['mobileCarrier']))
        except:
            panel.PhoneCarrier.SetSelection(0)
        panel.Paging.SetValue(str(data['paging']))
        if data['dob'] == '' or data['dob'] == None:
            pass
        else:
            panel.DOB.SetValue(data['dob'])
            foreground = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
            panel.DOB.SetForegroundColour(foreground)
            #calculate age:
            
            try: #Database provided date as string
                dob = date(*(time.strptime(str(data['dob']).encode('ascii'), '%Y-%m-%d')[0:3]))
            except TypeError:
                #Database provided date as time/datetime object.
                dob = date(*data['dob'])
            panel.AgeText.SetLabel(str(calculate_age(dob)))

        try:
            panel.Activity.SetStringSelection(self.db.GetActivity(data['activity']))
        except TypeError:
            panel.Activity.SetSelection(0)
        #Set the rooms accordingly:
        selection = panel.Activity.GetStringSelection()
        items = [ i['name'] for i in self.db.GetRoom(selection) ]
        items.insert(0, '') #Allow blank selection
        panel.Room.SetItems(items)
        panel.Room.SetStringSelection('')

        if data['activity'] != 0:
            #ID starts at 1 in database, but activity list starts at 0:
            if self.activities[data['activity']-1]['nametagEnable']:
                self.ToggleStateOn(panel.NametagToggle)
            else:
                self.ToggleStateOff(panel.NametagToggle)
            if self.activities[data['activity']-1]['parentTagEnable']:
                self.ToggleStateOn(panel.ParentToggle)
            else:
                self.ToggleStateOff(panel.ParentToggle)
        if data['noParentTag']: #Set parent-tag overrides if present:
            self.ToggleStateOff(panel.ParentToggle)
        if data['room'] == None or data['room'] == 0:
            pass
        else:
            panel.Room.SetStringSelection(self.db.GetRoomByID(data['room']))
        if data['parent1'] == None: data['parent1'] = ''
        panel.Parent1.SetValue(str(data['parent1']))
        if data['parent2'] == None: data['parent2'] = ''
        panel.Parent2.SetValue(str(data['parent2']))
        panel.Email.SetValue(str(data['parentEmail']))
        if data['medical'] == None: data['medical'] = ''
        panel.Medical.SetValue(str(data['medical']))
        if data['notes'] == None: data['notes'] = ''
        panel.Notes.SetValue(str(data['notes']))
        if data['picture'] != '' and data['picture'] != None:
            try:
                #Load and set the profile picture:
                path = self.PhotoStorage.getThumbnailPath(data['picture'])
                f = open(path)  #Check if file exists
                f.close()
                bmp = wx.Image(path).ConvertToBitmap()
                panel.ProfilePicture.SetBitmapLabel(bmp)
            except IOError:
                panel.ProfilePicture.SetBitmapLabel(self.NoPhoto128)
        #~ panel.CreatedText()
        self.RecordPanel.photo = data['picture']
        #For some reason trying to use '%c' as the format fails.
        try:
            panel.ModifiedText.SetLabel(time.strftime('%d %b %Y', 
                time.strptime(str(data['lastModified']), "%Y-%m-%dT%H:%M:%S")))
        except ValueError: #FIXME Format of test data was wrong: (????)
            panel.ModifiedText.SetLabel(str(data['lastModified'])[0:10])
        try:
            panel.ModifiedText.SetLabel(datetime.strftime(data['lastModified'], "%d %b %Y"))
        except (ValueError, TypeError):
            pass
        panel.ModifiedText.SetToolTipString(str(data['lastModified']))
        
        try:
            panel.CreatedText.SetLabel(time.strftime('%d %b %Y', 
                time.strptime(data['joinDate'], "%Y-%m-%d")))
        except TypeError:
            panel.CreatedText.SetLabel(time.strftime('%d %b %Y',
                time.strptime(str(data['joinDate']), '%Y-%m-%d')))
        except: #Date can't be determined, etc.
            panel.CreatedText.SetLabel('?')
        try:
            panel.LastSeenText.SetLabel(time.strftime('%d %b %Y',
                time.strptime(str(data['lastSeen']), "%Y-%m-%d")))
        except:
            panel.CreatedText.SetLabel('?')
            
        panel.CountText.SetLabel(str(data['count']))
            
        #~ if data['noParentTag']: self.ToggleStateOff(panel.ParentToggle)
        #Set barcode values:
        self.BarcodePanel.barcodes = [ j['value'] for i, j in enumerate(self.db.GetBarcodes(data['id'])) ]

        #Set status text:
        status = self.db.GetStatus(data['id'], True)
        if data['visitor']:
            rType = "Visitor"
        else:
            rType = "Member"

        if status['status'] == taxidi.STATUS_NONE:
            panel.StatusText.SetLabel(rType)
            panel.CheckinButton.Unbind(wx.EVT_BUTTON)
            panel.CheckinButton.SetLabel('Check-in')
            panel.CheckinButton.Bind(wx.EVT_BUTTON, self.SaveRecord)
        elif status['status'] == taxidi.STATUS_CHECKED_IN:
            if type(status['checkin']) in (str, unicode):
                checkin = datetime.strftime(datetime.strptime(str(status['checkin']), "%Y-%m-%dT%H:%M:%S"), "%H:%M:%S")
            elif type(status['checkin']) is datetime:
                checkin = datetime.strftime(status['checkin'], "%H:%M:%S")
            else:
                checkin = None
            panel.StatusText.SetLabel(
                "{0} - Checked-in at {1}".format(
                rType,
                checkin))
            panel.CheckinButton.Unbind(wx.EVT_BUTTON)
            panel.CheckinButton.SetLabel('Check-out')
            panel.CheckinButton.Bind(wx.EVT_BUTTON, self.OnCheckOut)
        elif status['status'] == taxidi.STATUS_CHECKED_OUT:
            if type(status['checkout']) in (str, unicode):
                checkout = datetime.strftime(datetime.strptime(str(status['checkout']), "%Y-%m-%dT%H:%M:%S"), "%H:%M:%S")
            elif type(status['checkout']) is datetime:
                checkout = datetime.strftime(status['checkout'], "%H:%M:%S")
            else:
                checkout = None
            panel.StatusText.SetLabel(
                "{0} - Checked out at {1}".format(rType, checkout))
            panel.CheckinButton.Unbind(wx.EVT_BUTTON)
            panel.CheckinButton.SetLabel('Check-in')
            panel.CheckinButton.Bind(wx.EVT_BUTTON, self.SaveRecord)

        pane = self.BarcodePanel
        pane.code1.SetValue('')
        pane.code2.SetValue('')
        pane.code3.SetValue('')
        pane.code4.SetValue('')
        pane.code5.SetValue('')
        pane.code6.SetValue('')
        #~ codes = self.db.GetBarcodes(
        for i in range(len(self.BarcodePanel.barcodes)):
            self.BarcodePanel.codes[i].SetValue(str(self.BarcodePanel.barcodes[i]))
        panel.Email.SetBackgroundColour(wx.NullColour)
        panel.Phone.SetBackgroundColour(wx.NullColour)
        panel.DOB.SetBackgroundColour(wx.NullColour)

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
        self.services = self.db.GetServices()
        self.SetServices()  #Setup the service selections
        #Setup printing if needed:
        import printing
        self.printing = printing.Main()

    def OnChangeService(self, event):
        choice = event.GetEventObject()
        if conf.as_bool(conf.config['config']['autoServices']):
            if self.services[choice.GetSelection()] == self.GetCurrentService(self.services):
                #Switched back to current automatic service.  Return to time-table operation:
                self.serviceManual = False
                self.service = self.services[choice.GetSelection()]
                notify.info("Service Change", "Changed to currently active service. "\
                    "Automatic service changes are now enabled.")
            else: #Changed service manually. Show warning and stop automatic checking.
                self.serviceManual = True
                self.service = self.services[choice.GetSelection()]
                notify.info("Manual Service Change", "The active service was manually changed "\
                    "to <span weight=\"bold\">{0}</span>.  Service timings will be ignored until changed back to "\
                    "the currently active service.".format(self.service['name']))
        else: #Change service normally:
            self.service = self.services[choice.GetSelection()]


    def GetCurrentService(self, services):
        today = date.today()
        now = time.strftime('%H:%M:%S', time.localtime())
        #Determine the current service and set it as the selection:
        for i in range(len(services)):
            if services[i]['day'] == date.isoweekday(today) or services[i]['day'] == 0:
                delta = datetime.strptime(str(services[i]['endTime']), '%H:%M:%S') - datetime.strptime(now, '%H:%M:%S')
                if delta.days < 0:  #Service has ended
                    pass
                if services[i]['time'] == '': #Assume All day
                    delta2 = datetime.strptime('00:00:00', '%H:%M:%S') - datetime.strptime(now, '%H:%M:%S')
                else:
                    delta2 = datetime.strptime(str(services[i]['time']), '%H:%M:%S') - datetime.strptime(now, '%H:%M:%S')
                if delta.days == 0 and delta2.days < 0:
                    #Currently active service.  Set it as the selection.
                    return services[i]
        #else:
        return services[0]

    def SetServices(self):

        services = self.db.GetServices()
        if len(self.services) == 0:
            if len(self.services) == 1 and \
                self.services[0]['name'] == 'None Defined':
                notify.warning('No Services', 'Please add a service '\
                    'before continuing.')
            self.services = [ {'name': 'None Defined',
                               'day' : 0, 'time': '00:00:00',
                               'endTime': '23:59:59' }, ]
        else:
            self.services = services
        serviceList = [ i['name'] for i in self.services ]
        self.SearchPanel.ServiceSelection.SetItems(serviceList)

        self.serviceManual = False #Flag used to descern between manual changes and automatic (time table) ones.
        self.service = self.services[0] #Remember the current service
        if conf.as_bool(conf.config['config']['autoServices']):
            #Determine the current service and set it as the selection:
            self.service = self.GetCurrentService(self.services)
            self.SearchPanel.ServiceSelection.SetStringSelection(self.service['name'])

    def StartCheckin(self, event):
        conf.config.reload()
        self.setupDatabase()
        if self.PerformAuthentication(main=True):
            self.BeginCheckinRoutine(None)
        else:
            self.db.close()

    def OnParentSearch(self, event):
        win = ParentSearch(self.frame, wx.SIMPLE_BORDER)
        win.NewButton.Bind(wx.EVT_BUTTON, self.OnNewParent)
        btn = event.GetEventObject()
        win.callback = btn #Store the calling object for later
        pos = btn.ClientToScreen( (0,0) )
        sz =  btn.GetSize()
        win.Position(pos, (0, sz[1]))
        win.Popup()

    def OnNewParent(self, event):
        btn = event.GetEventObject()
        #Close the old pop-up, getting the old coordinates
        oldwin = btn.GetParent()
        size = oldwin.GetPosition()
        #Create the new pop-up
        win = NewParent(self.frame, wx.SIMPLE_BORDER | wx.TAB_TRAVERSAL)
        #copy the original calling object:
        win.callback = oldwin.callback
        oldwin.Destroy() #And destroy the old object

        win.Phone.Bind(wx.EVT_TEXT, self.FormatParentPhoneLive) #phone validator
        win.SetPosition(size)
        win.Popup()

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

#Transient pop-up for searching and linking parent records:
class ParentSearch(wx.PopupTransientWindow):
    """
    Transient pop-up for searching for a parent to link (internal or from
    ChurchInfo, FellowshipOne, usw.
    """
    def __init__(self, parent, style):
        wx.PopupTransientWindow.__init__(self, parent, style)
        box1 = wx.BoxSizer(wx.VERTICAL)
        box2 = wx.BoxSizer(wx.HORIZONTAL)

        st = wx.StaticText(self, wx.ID_ANY, "Parent search")
        box2.Add(st, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        box2.AddStretchSpacer()

        self.NewButton = wx.Button(self, wx.ID_ANY, "New")
        box2.Add(self.NewButton, 0, wx.ALL | wx.ALIGN_CENTRE_VERTICAL, 5)

        box1.Add(box2, 0, wx.EXPAND, 5)
        self.ListBox = wx.ListBox(self, wx.ID_ANY, style = wx.LB_SINGLE)
        self.ListBox.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL, False))

        box1.Add(self.ListBox, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(box1)
        self.SetSize((336, 142))
        self.Layout()

class NewParent(wx.PopupTransientWindow):
    """
    Transient pop-up for adding a new parent when creating a record.
    """
    def __init__(self, parent, style):
        wx.PopupTransientWindow.__init__(self, parent, style)
        box1 = wx.BoxSizer(wx.VERTICAL)
        box2 = wx.BoxSizer(wx.HORIZONTAL)

        st = wx.StaticText(self, wx.ID_ANY, 'New parent')
        box2.Add(st, 0, wx.ALL | wx.ALIGN_CENTRE_VERTICAL, 5)
        box2.AddStretchSpacer()

        self.SaveButton = wx.Button(self, wx.ID_ANY, "Save")
        box2.Add(self.SaveButton, 0, wx.ALL | wx.ALIGN_CENTRE_VERTICAL, 5)

        box1.Add(box2, 0, wx.EXPAND, 5)

        box3 = wx.BoxSizer(wx.HORIZONTAL)
        phonest = wx.StaticText(self, wx.ID_ANY, "Phone (optional):")
        box3.Add(phonest, 0, wx.ALL | wx.ALIGN_CENTRE_VERTICAL, 5)

        self.Phone = wx.TextCtrl(self, wx.ID_ANY, style = wx.TE_CENTRE)
        self.Phone.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL, False))
        box3.Add(self.Phone, 1, wx.ALL | wx.ALIGN_CENTRE_VERTICAL, 5)
        box1.Add(box3, 0, wx.EXPAND, 5)

        box4 = wx.BoxSizer(wx.HORIZONTAL)
        carrierst = wx.StaticText(self, wx.ID_ANY, "Carrier:")
        box4.Add(carrierst, 0, wx.ALL | wx.ALIGN_CENTRE_VERTICAL, 5)

        self.CarrierSelection = wx.Choice(self, wx.ID_ANY, choices=['Land Line',])
        box4.Add(self.CarrierSelection, 1, wx.ALL | wx.ALIGN_CENTRE_VERTICAL, 5)
        box1.Add(box4, 0, wx.EXPAND, 5)

        self.SetSizer(box1)
        self.SetSize((336, 142))
        self.Layout()



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

def calculate_age(born):
    today = date.today()
    try: # raised when birth date is February 29 and the current year is not a leap year
        birthday = born.replace(year=today.year)
    except ValueError:
        birthday = born.replace(year=today.year, day=born.day-1)
    if birthday > today:
        return today.year - born.year - 1
    else:
        return today.year - born.year

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
        import wx.lib.delayedresult as delayedresult
        import taxidi
        import conf
        import SearchResultsList
        import dialogues
        import hashlib
        import validate
        import time
        from datetime import date, datetime
        from dateutil.relativedelta import relativedelta


        if conf.as_bool(conf.config['webcam']['enable']) == True:
            import webcam
        else:
            #Import file selection dialogue instead
            import wx.lib.imagebrowser as ib
            import webcam #for maniuplating database photos

        #Libnotify?
        if conf.as_bool(conf.config['interface']['libnotify']):
            from notify import local as notify
        else: #Load dummy module to supress messages
            from notify.local import Dummy as notify

        try:
            app = MyApp(0)
            app.MainLoop()
        except:
            import sys, traceback
            xc = traceback.format_exception(*sys.exc_info())
            wx.MessageBox(''.join(xc))


#~ app = MyApp(0)
#~ app.MainLoop()
