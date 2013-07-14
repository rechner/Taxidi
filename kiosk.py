#!/usr/bin/env python
#-*- coding:utf-8 -*-

#TODO: (BUG, LOW PRIORITY): Fix size issue on screens > (1024x786)
#TODO: Fix birthday code
#TODO: Add/fix logging

#Global imports
import wx
import datetime
from datetime import date
import time
import subprocess
import wx.lib.delayedresult as delayedresult
import hashlib
from optparse import OptionParser #for CLI options
import logging
import traceback

#Set locale to system default (for date/time format):
import locale
locale.setlocale(locale.LC_ALL, '')

#parse command line:
parser = OptionParser(usage="Usage: %prog [options]")
parser.add_option("--verbose", action="store_true", 
                  dest="verbose", default=False,
                  help="Enable verbose logging to console")
parser.add_option("-q", "--quiet", action="store_false", 
                  dest="verbose", help="Supress output to console")
parser.add_option("-f", "--fullscreen", action="store_true",
                  dest="fullscreen", help="Force opening in fullscreen")
parser.add_option("-w", "--windowed", action="store_false",
                  dest="fullscreen", help="Force opening in a window")
parser.add_option("-l", "--location", dest="location",
                  help="Name of this kiosk (for reporting)")
(opts, args) = parser.parse_args()

#Local imports
import conf
import taxidi
import SearchResultsList
import webcam #for storage class
import printing
import dialogues

#libnotify
if conf.as_bool(conf.config['interface']['libnotify']):
    from notify import local as notify
else: #Load dummy module to supress messages
    from notify.local import Dummy as notify

#Some globals for now (no theme files yet)
global themeTextColour
themeTextColour = "white"
themeBackgroundColour = "black"

class SearchPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        #Background Image
        wximg = wx.Image("resources/themes/air/search.png")
        wxbanner=wximg.ConvertToBitmap()
        self.bitmap = wx.StaticBitmap(self,-1,wxbanner,(0,0))
        self.SetBackgroundColour("black")
        
        #Set the cursor (blank for production(?))
        #~ cursor = wx.StockCursor(wx.CURSOR_CROSS)
        #~ self.bitmap.SetCursor(cursor)
        
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        
        self.AdminButton = wx.Button(self, wx.ID_ANY, "Date\nTime\n(Service Name Here)", style=wx.NO_BORDER)
        self.AdminButton.SetForegroundColour("white")
        sizer1.Add(self.AdminButton, 0, 0, 5)
        
        fgsizer = wx.FlexGridSizer(3, 3, 0, 0)
        fgsizer.AddGrowableCol(0)
        fgsizer.AddGrowableCol(1)
        fgsizer.AddGrowableCol(2)
        fgsizer.AddGrowableRow(1)
        fgsizer.AddGrowableRow(3)
        fgsizer.SetFlexibleDirection(wx.BOTH)
        fgsizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)
        
        fgsizer.AddStretchSpacer()
        fgsizer.AddStretchSpacer()
        fgsizer.AddStretchSpacer()
        fgsizer.AddStretchSpacer()
        fgsizer.AddStretchSpacer()
        fgsizer.AddStretchSpacer()
        fgsizer.AddStretchSpacer()
        
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        
        self.Search = wx.TextCtrl(self, wx.ID_ANY, size=(250, 50), style=wx.TE_CENTRE|wx.TE_PROCESS_ENTER)
        self.Search.SetFont(wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL, False))
        
        sizer2.Add(self.Search, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 5)
        
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        
        self.KeyboardButton = wx.Button(self, wx.ID_ANY, u"⌨", size=(-1, 40))
        self.KeyboardButton.SetFont(wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL, False))
        self.KeyboardButton.Bind(wx.EVT_BUTTON, self.ShowKeyboard)
        
        sizer3.Add(self.KeyboardButton, 0, wx.EXPAND | wx.ALIGN_CENTRE_VERTICAL, 5)
        
        self.SearchButton = wx.Button(self, wx.ID_ANY, "Search", size=(-1, 40))
        self.SearchButton.SetDefault()
        sizer3.Add(self.SearchButton, 1, wx.EXPAND | wx.LEFT, 5)
        
        sizer2.Add(sizer3, 1, wx.EXPAND | wx.TOP, 5)
        
        fgsizer.Add(sizer2, 0, wx.ALIGN_CENTRE_HORIZONTAL|wx.ALIGN_CENTRE_VERTICAL, 5)
        
        fgsizer.AddStretchSpacer()
        fgsizer.AddStretchSpacer()
        fgsizer.AddStretchSpacer()
        
        sizer1.Add(fgsizer, 1, wx.EXPAND, 5)
        
        self.SetSizer(sizer1)
        self.SetSize((1024, 768))
        self.Layout()
        
        self.Search.SetFocus()
        self.Bind(wx.EVT_SIZE, self.on_size)
        
        self.service = '?'
        
        #~ self.timer = NotifyTimer(self)
        #~ self.timer.Start(1000)
        
        
    def on_size(self, event):
        event.Skip()
        panel = event.GetEventObject()
        panel = self
        size = panel.GetParent().GetSize()
        panel.CentreOnParent(dir=wx.BOTH)
        #~ panel.SetPosition(( int((size[0]-1024)/2), 0 ))
        panel.SetSize((1024, 768))
        panel.Layout()
        
    def ShowKeyboard(self, event):
        try:
            subprocess.Popen(('/usr/bin/onboard', '-x', '0', 
                          '-y', '470', '-s', '1024x300'))
        except OSError:
            print "Onboard is not installed.  Unable to open keyboard"
            notify.warning('Onboard not installed', 
                'Unable to open on-screen keyboard')
        self.Search.SetFocus()
        

class NotifyTimer(wx.Timer):
    """
    Timer class to update date/time display in search panel.
    """
    def __init__(self, parent):
        wx.Timer.__init__(self)
        self.parent = parent

    def Notify(self):
        if conf.as_bool(conf.config['config']['autoServices']):
            #Determine the current service and set it as the selection:
            self.parent.service = self.parent.GetCurrentService(self.parent.services)
            self.parent.SearchPanel.service = self.parent.service['name']
        
        date = datetime.datetime.now().strftime("%d %b %Y")
        time = datetime.datetime.now().strftime("%X")
        self.parent.SearchPanel.AdminButton.SetLabel("{0}\n{1}\n({2})".format(date,
                                         time, self.parent.SearchPanel.service))
                                               

class ActionPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        #Background Image
        wximg = wx.Image("resources/themes/air/single.png")
        wxbanner=wximg.ConvertToBitmap()
        self.bitmap = wx.StaticBitmap(self,-1,wxbanner,(0,0))
        self.SetBackgroundColour("black")
        
        box1 = wx.BoxSizer( wx.VERTICAL )
        fgSizer = wx.FlexGridSizer( 3, 3, 0, 0 )
        fgSizer.AddGrowableCol( 0 )
        fgSizer.AddGrowableCol( 1 )
        fgSizer.AddGrowableCol( 2 )
        fgSizer.AddGrowableRow( 1 )
        fgSizer.AddGrowableRow( 3 )
        fgSizer.SetFlexibleDirection( wx.BOTH )
        fgSizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )        
    
        fgSizer.AddStretchSpacer()
        fgSizer.AddStretchSpacer()
        fgSizer.AddStretchSpacer()
        fgSizer.AddStretchSpacer()
        fgSizer.AddStretchSpacer()  
        fgSizer.AddStretchSpacer()
        fgSizer.AddStretchSpacer()
    
        box2 = wx.BoxSizer( wx.VERTICAL )
    
        st1 = wx.StaticText( self, wx.ID_ANY, "Select an action below to complete check-in.", wx.DefaultPosition, wx.DefaultSize, 0 )
        st1.SetFont( wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL, False) )
        st1.SetForegroundColour(themeTextColour)
    
        box2.Add( st1, 0, wx.ALL, 5 );
    
        box3 = wx.BoxSizer( wx.HORIZONTAL )
    
        self.Picture = wx.StaticBitmap(self, wx.ID_ANY, wx.Image("resources/icons/no-photo-128.png").ConvertToBitmap())
        box3.Add( self.Picture, 0, wx.ALL, 5 )
    
        box4 = wx.BoxSizer( wx.VERTICAL )
    
        box5 = wx.BoxSizer( wx.HORIZONTAL )
    
        self.CheckinButton = wx.Button(self, wx.ID_ANY, "Check-in")
        box5.Add( self.CheckinButton, 1, wx.ALL|wx.EXPAND, 5 )
    
        self.MultiServiceButton = wx.Button(self, wx.ID_ANY, "     Check-in for\nMultiple Services")
        box5.Add( self.MultiServiceButton, 1, wx.ALL|wx.EXPAND, 5 )
    
        box4.Add( box5, 1, wx.EXPAND, 5 )
    
        self.CancelButton = wx.Button(self, wx.ID_ANY, "Cancel", size=(-1, 45))
        box4.Add(self.CancelButton, 0, wx.ALL | wx.EXPAND, 5)
    
        box3.Add(box4, 1, wx.EXPAND, 5)
        box2.Add(box3, 1, wx.EXPAND, 5)
    
        stline = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL );
        box2.Add( stline, 0, wx.EXPAND | wx.ALL, 5 );
    
        stSizer = wx.BoxSizer(wx.VERTICAL)  

        self.NameText = wx.StaticText(self, wx.ID_ANY, "Firstname Lastname")
        self.NameText.Wrap(-1)
        self.NameText.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.BOLD, False))
        self.NameText.SetForegroundColour(themeTextColour)
        stSizer.Add(self.NameText, 0, wx.ALL, 5)
    
        self.PhoneText = wx.StaticText(self, wx.ID_ANY, "Phone: (###) ###-###")
        self.PhoneText.SetFont(wx.Font(13, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL, False))
        stSizer.Add(self.PhoneText, 0, wx.ALL, 5)
        self.PhoneText.SetForegroundColour(themeTextColour)
    
        self.ActivityText = wx.StaticText(self, wx.ID_ANY, "Activity:")
        self.ActivityText.SetForegroundColour(themeTextColour)
        self.ActivityText.SetFont(wx.Font(13, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL, False))
        stSizer.Add(self.ActivityText, 0, wx.ALL, 5)
        
        self.RoomText = wx.StaticText(self, wx.ID_ANY, "Room:")
        self.RoomText.SetFont(wx.Font(13, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL, False))
        stSizer.Add(self.RoomText, 0, wx.ALL, 5)
        self.RoomText.SetForegroundColour(themeTextColour)
        
        self.StatusText = wx.StaticText(self, wx.ID_ANY, "Member")
        self.StatusText.SetFont(wx.Font(13, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL, False))
        stSizer.Add(self.StatusText, 0, wx.ALL, 5)
        self.StatusText.SetForegroundColour(themeTextColour)
    
        box2.Add( stSizer, 1, wx.EXPAND, 5 );
    
        fgSizer.Add( box2, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 5 );
    
        fgSizer.AddStretchSpacer()
        fgSizer.AddStretchSpacer()
        fgSizer.AddStretchSpacer()
    
        box1.Add( fgSizer, 1, wx.EXPAND, 5 )
    
        self.SetSizer( box1 )
        self.Layout()
        
        self.Bind(wx.EVT_SIZE, self.on_size)
        
    def SetData(self, name, phone, activity, room, status, picture=None):
        if picture == None:
            picture = "resources/icons/no-photo-128.png"
            
        self.NameText.SetLabel(name)
        self.PhoneText.SetLabel("Phone: {0}".format(phone))
        self.ActivityText.SetLabel("Activity: {0}".format(activity))
        self.RoomText.SetLabel("Room: {0}".format(room))
        self.StatusText.SetLabel("Status: {0}".format(status))
        
        try:
            self.Picture.SetBitmap(wx.Image(picture).ConvertToBitmap())
        except:
            self.Picture.SetBitmap(wx.Image("resources/icons/no-photo-128.png").ConvertToBitmap())
        
        
        
    def on_size(self, event):
        event.Skip()
        panel = event.GetEventObject()
        panel = self
        size = panel.GetParent().GetSize()
        panel.CentreOnParent(dir=wx.BOTH)
        #~ panel.SetPosition(( int((size[0]-1024)/2), 0 ))
        #~ panel.bitmap.SetPosition(( int((size[0]-1024)/2), 0 ))
        panel.SetSize((1024, 768))
        panel.Layout()
        

class BirthdayPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)        
        #Background Image
        self.wximg = wx.Bitmap("resources/themes/air/birthday.png")
        self.CloseButton = wx.Button(self, wx.ID_CLOSE, "", size=(300,50), pos=(362,650))        
        
        self.SetSize((1024, 768))
        self.Layout()
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        
    def on_size(self, event):
        event.Skip()
        panel = event.GetEventObject()
        panel = self
        size = panel.GetParent().GetSize()
        panel.CentreOnParent(dir=wx.BOTH)
        #~ panel.SetPosition(( int((size[0]-1024)/2), 0 ))
        #~ panel.bitmap.SetPosition(( int((size[0]-1024)/2), 0 ))
        panel.SetSize((1024, 768))
        panel.Layout()

    #proper method as pulled from blog.pythonlibrary.org
    def OnEraseBackground(self, event):
        """
        Add a picture to the background
        """
        # yanked from ColourDB.py
        dc = event.GetDC()
 
        if not dc:
            dc = wx.ClientDC(self)
            rect = self.GetUpdateRegion().GetBox()
            dc.SetClippingRect(rect)
        dc.Clear()
        dc.DrawBitmap(self.wximg, 0, 0)

        
class ResultsPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        #Background Image
        wximg = wx.Image("resources/themes/air/results.png")
        wxbanner=wximg.ConvertToBitmap()
        self.bitmap = wx.StaticBitmap(self,-1,wxbanner,(0,0))
        self.SetBackgroundColour("black")
        
        box1 = wx.BoxSizer( wx.VERTICAL )
    
        fgSizer = wx.FlexGridSizer( 3, 3, 0, 0 )
        #~ fgSizer.AddGrowableCol( 0 );
        fgSizer.AddGrowableCol( 1 );
        #~ fgSizer.AddGrowableCol( 2 );
        fgSizer.AddGrowableRow( 1 );
        fgSizer.AddGrowableRow( 3 );
        fgSizer.SetFlexibleDirection( wx.BOTH );
        fgSizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED );
        
        fgSizer.AddSpacer((1, 160))
        fgSizer.AddSpacer((1, 160))
        fgSizer.AddSpacer((1, 160))
        #~ fgSizer.AddStretchSpacer()
        fgSizer.AddSpacer((10, 1))
        fgSizer.AddStretchSpacer()
        fgSizer.AddSpacer((10, 1))
        #~ fgSizer.AddStretchSpacer()
        fgSizer.AddSpacer((10, 1))
        #~ fgSizer.AddStretchSpacer()
        
        box2 = wx.BoxSizer( wx.VERTICAL )
        
        #The results list sub-panel:
        self.ResultsList = SearchResultsList.SearchResultsPanel(self, size=(960, 450))
        self.ResultsList.SetMinSize((900, 450))
        box2.Add(self.ResultsList, 8, wx.ALL|wx.EXPAND, 5)
            
        buttonSizer = wx.BoxSizer( wx.HORIZONTAL )
        
        self.CancelButton = wx.Button(self, wx.ID_BACKWARD, "", size=( -1,50 ))
        buttonSizer.Add( self.CancelButton, 2, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5 )
        
        buttonSizer.AddStretchSpacer()
        
        self.MultiServiceButton = wx.Button(self, wx.ID_ANY, "Check-in for Multiple Services", size=( -1,50 ));
        buttonSizer.Add( self.MultiServiceButton, 2, wx.EXPAND|wx.LEFT, 5 );
        
        self.CheckinButton = wx.Button(self, wx.ID_ANY, "Check-in", size=( -1,50 ));
        self.CheckinButton.SetDefault(); 
        buttonSizer.Add( self.CheckinButton, 2, wx.EXPAND|wx.LEFT, 5 );
        
        box2.Add(buttonSizer, 1, wx.EXPAND|wx.TOP, 5)
        
        fgSizer.Add( box2, 2, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 5 )
        
        #~ fgSizer.AddStretchSpacer()
        fgSizer.AddSpacer((10, 1))
        #~ fgSizer.AddStretchSpacer()
        fgSizer.AddSpacer((10, 1))
        #~ fgSizer.AddStretchSpacer()
        fgSizer.AddSpacer((10, 1))
        #~ fgSizer.AddStretchSpacer()
        fgSizer.AddSpacer((10, 1))
        
        box1.Add(fgSizer, 1, wx.EXPAND, 5 )
        
        self.SetSizer(box1)
        
        self.SetSize((1024, 768))
        self.Layout()
        
        self.Bind(wx.EVT_SIZE, self.on_size)
        
    def on_size(self, event):
        event.Skip()
        panel = event.GetEventObject()
        panel = self
        size = panel.GetParent().GetSize()
        panel.CentreOnParent(dir=wx.BOTH)
        #~ panel.SetPosition(( int((size[0]-1024)/2), 0 ))
        #~ panel.bitmap.SetPosition(( int((size[0]-1024)/2), 0 ))
        panel.SetSize((1024, 768))
        panel.Layout()
    
class AdminDialog(wx.Dialog):
    """
    Kiosk administration dialog.
    """
    def __init__(self, parent, id):
        wx.Dialog.__init__(self, parent, id, 'Kiosk Administration', size=(340,300))
        self.InitUI()
        
    def InitUI(self):
        box1 = wx.BoxSizer(wx.VERTICAL)
        
        box2 = wx.BoxSizer(wx.HORIZONTAL)
        
        st = wx.StaticText(self, wx.ID_ANY, "Service:")
        box2.Add(st, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
        
        self.ServiceSelection = wx.Choice(self, wx.ID_ANY, size=(-1,40))
        self.ServiceSelection.Disable()
        box2.Add(self.ServiceSelection, 1, wx.ALL, 5 )
        
        box1.Add( box2, 0, wx.EXPAND, 5 );
        
        sbox = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, "Actions" ), wx.VERTICAL );
        
        ExitButton = wx.Button( self, wx.ID_ANY, "Exit to Operating System", size=( -1,50 ));
        ExitButton.Bind(wx.EVT_BUTTON, self.OnExit)
        sbox.Add( ExitButton, 0, wx.ALL|wx.EXPAND, 5 );
        
        ShutdownButton = wx.Button( self, wx.ID_ANY, "Shutdown", size=( -1,50 ))
        ShutdownButton.Bind(wx.EVT_BUTTON, self.OnShutdown)
        sbox.Add( ShutdownButton, 0, wx.ALL|wx.EXPAND, 5 );
        
        box1.Add( sbox, 0, wx.ALL|wx.EXPAND, 5 );
        
        CloseButton = wx.Button( self, wx.ID_ANY, "Close", size=( -1,50 ));
        CloseButton.Bind(wx.EVT_BUTTON, self.CloseDialog)
        box1.Add( CloseButton, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND, 5 );
        
        self.SetSizer( box1 )
        self.Layout()
        
    def CloseDialog(self, event):
        self.Close()
        
    def OnExit(self, event):
        self.EndModal(wx.ID_EXIT)
        
    def OnShutdown(self, event):
        self.EndModal(wx.ID_STOP)

class KioskApp(wx.App):
    """
    The main program loop class
    """
    def OnInit(self):
        self.log = logging.getLogger(__name__)  #Setup logging
        #Setup the frame:
        self.frame = wx.Frame(None, size=wx.DisplaySize())
        if opts.fullscreen is None:
            if conf.as_bool(conf.config['interface']['fullscreen']):
                self.frame.ShowFullScreen(True)
        elif opts.fullscreen:
            self.frame.ShowFullScreen(True)
        self.frame.SetBackgroundColour(themeBackgroundColour)
        
        #Add the panels:
        self.SearchPanel = SearchPanel(self.frame)
        self.ActionPanel = ActionPanel(self.frame)
        self.ResultsPanel = ResultsPanel(self.frame)
        self.BirthdayPanel = BirthdayPanel(self.frame)
        
        #Hide all except for search:
        self.ActionPanel.Hide()
        self.ResultsPanel.Hide()
        self.BirthdayPanel.Hide()
        
        #Handle resizing the frame:
        self.frame.Bind(wx.EVT_SIZE, self._on_size)
        
        #Bind button actions (SearchPanel):
        self.SearchPanel.SearchButton.Bind(wx.EVT_BUTTON, self.OnSearch)
        self.SearchPanel.Search.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
        self.SearchPanel.Search.Bind(wx.EVT_TEXT, self.ResetSearchColour)
        self.SearchPanel.AdminButton.Bind(wx.EVT_BUTTON, self.OnAdmin)
        
        #Bind button actions (ActionPanel):
        self.ActionPanel.CancelButton.Bind(wx.EVT_BUTTON, self.ActionPanelCancel)
        self.ActionPanel.CheckinButton.Bind(wx.EVT_BUTTON, self.OnCheckin)
        self.ActionPanel.MultiServiceButton.Bind(wx.EVT_BUTTON, self.OnCheckin)
        
        #Bind button actions (ResultsPanel):
        self.ResultsPanel.CancelButton.Bind(wx.EVT_BUTTON, self.ResultsPanelCancel)
        self.ResultsPanel.CheckinButton.Bind(wx.EVT_BUTTON, self.OnMultiCheckin)
        self.ResultsPanel.MultiServiceButton.Bind(wx.EVT_BUTTON, self.OnMultiCheckinMultiService)
        
        #Bind button actions (BirthdayPanel):
        self.BirthdayPanel.CloseButton.Bind(wx.EVT_BUTTON, self.BirthdayPanelClose)
        
        #Show the frame:
        self.frame.Show()
        
        #Setup database:
        self.setupDatabase()
        
        #Setup webcam photo storage:
        self.PhotoStorage = webcam.Storage()
        
        #Setup printing:
        self.printing = printing.Main()
        
        #Init some variables:
        self.jobID = 0
        self.multiJobID = 0
        
        #Start your engines:
        self.timer = NotifyTimer(self)
        self.timer.Start(1000)
        
        return True
        
    def OnAdmin(self, event):
        if self.PerformAuthentication():
            #Open admin dialog
            dlg = AdminDialog(self.frame, wx.ID_ANY)
            ret = dlg.ShowModal()
            dlg.Destroy()
            if ret == wx.ID_EXIT:
                self.Close()
            elif ret == wx.ID_STOP:
                self.Shutdown()
            self.SearchPanel.Search.SetFocus()

    def Close(self):
        self.db.close()
        self.frame.Destroy()
        exit()
        
    def Shutdown(self):
        dlg = wx.MessageDialog(self.frame, 
            "Do you really want to shutdown?",
            "Confirm Shutdown", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            self.db.close()
            self.frame.Destroy()
            subprocess.call(('/usr/bin/sudo', '/sbin/init', '0'))
            exit()
        
        
    def setupDatabase(self):
        #Read user config and import the appropriate database.
        if conf.config['database']['driver'].lower() == 'sqlite':
            datafile = conf.homeAbsolutePath(conf.config['database']['file'])
            import dblib.sqlite as database
            database.debug = opts.verbose
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
            database.debug = opts.verbose
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
                
        self.activities = self.db.GetActivities()
        self.services = self.db.GetServices()
        self.SetServices()
        
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

        if conf.as_bool(conf.config['config']['autoServices']):
            #Determine the current service and set it as the selection:
            self.service = self.GetCurrentService(self.services)
            self.SearchPanel.service = self.service['name']
            
    def GetCurrentService(self, services):
        today = date.today()
        now = time.strftime('%H:%M:%S', time.localtime())
        #Determine the current service and set it as the selection:
        for i in range(len(services)):
            if services[i]['day'] == date.isoweekday(today) or services[i]['day'] == 0:
                delta = datetime.datetime.strptime(str(services[i]['endTime']), '%H:%M:%S') - datetime.datetime.strptime(now, '%H:%M:%S')
                if delta.days < 0:  #Service has ended
                    pass
                if services[i]['time'] == '': #Assume All day
                    delta2 = datetime.datetime.strptime('00:00:00', '%H:%M:%S') - datetime.datetime.strptime(now, '%H:%M:%S')
                else:
                    delta2 = datetime.datetime.strptime(str(services[i]['time']), '%H:%M:%S') - datetime.datetime.strptime(now, '%H:%M:%S')
                if delta.days == 0 and delta2.days < 0:
                    #Currently active service.  Set it as the selection.
                    return services[i]
        #else:
        return services[0]

    def OnCheckin(self, event):
        button = event.GetEventObject()
        panel = button.GetParent()
        
        activity = self.db.GetActivityById(self.ActionPanel.data['activity']) #as dict
        #~ activity = self.ActionPanel.data['activity']
        room = self.db.GetRoomByID(self.ActionPanel.data['room'])
        #~ room = self.ActionPanel.data['room']
        services = (self.SearchPanel.service,)
        index = self.ActionPanel.data['id']
        name = self.ActionPanel.data['name']
        surname = self.ActionPanel.data['lastname']
        pagingValue = self.ActionPanel.data['paging']
        medical = self.ActionPanel.data['medical']
        parentEnable = not self.ActionPanel.data['noParentTag']
        
        if button == panel.MultiServiceButton:
            #Prompt the user for services selection:
            self.services = self.db.GetServices()
            dlg = SearchResultsList.MultiServiceDialog(self.frame, wx.ID_ANY, self.services)
            if dlg.ShowModal() == wx.ID_OK:
                #print "DEBUG"
                #print dlg.selected
                #print [ i ['name'] for i in dlg.selected ]
                if dlg.selected != []: #Make sure something's selected
                    services = [ i['name'] for i in dlg.selected ]
                    data = [{ 'id': index, 'name': name, 'lastname': surname,
                         'paging': pagingValue, 'medical': medical,
                         'room': room,
                         'activity': activity, 'nametag': True,
                         'parentTag': parentEnable }]
                    self.DoMultiCheckin(services, data)
                else:
                    notify.info("Checkin incomplete", "No services selected.")
                    dlg.Destroy()
                    return
            else:
                dlg.Destroy()
                return
            dlg.Destroy()
              
        self.jobID += 1
        #~ self._checkinProducer(0, self.ActionPanel.data, services, activity, room, False)
        delayedresult.startWorker(self._checkinConsumer, self._checkinProducer,
                                  wargs=(self.jobID, self.ActionPanel.data,
                                         services, activity, room, False),
                                  jobID=self.jobID)
        time.sleep(0.4)  #FIXME: Give the database time to settle (sqlite3 thread-safe?)
        self.ActionPanelCancel(None)        
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
            
        try:
            if opts.location is not None:
                location = opts.location
            else:
                location = conf.config['config']['name']
        except AttributeError:
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
        if True:
            if secure == None:
                barcode = False
            else:
                barcode = True
            #Generate the nametag:
            self.printing.nametag(theme=activity['nametag'], room=room,
                                  first=data['name'], last=data['lastname'],
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


        if not data['noParentTag']: #Print parent tag if needed:
            if secure != None:
                barcode = False
            else:
                barcode = True
            link = activity['parentURI']
            self.printing.parent(theme=activity['nametag'], room=room,
                                 first=data['name'], last=data['lastname'],
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

        wx.CallLater(4000, self.printing.cleanup, trash) #Delete temporary files later
        return jobID
        
    def _checkinConsumer(self, delayedResult):
        jobID = delayedResult.getJobID()
        assert jobID == self.jobID
        try:
            result = delayedResult.get()
        except Exception, exc:
            notify.error("Thread Error", "Result for job %s raised exception: %s" % (jobID, exc) )
            self.log.error("Thread Error: Result for job %s raised exception: %s" % (jobID, exc))
            print traceback.format_exc()
            self.log.error(traceback.format_exc())
            raise
            return
                
    def OnMultiCheckin(self, event):
        checked = self.ResultsPanel.ResultsList.GetSelected() #Index of checked items
        copyofChecked = checked[:] #Create a new copy of the list,
        #since copyofChecked = checked would just create a new reference
        #to checked, causing manipulation problems.  See
        #http://henry.precheur.org/python/copy_list

        #Remove those already marked as checked-in.
        for i in copyofChecked:
            if self.ResultsPanel.ResultsList.results[i]['status'] == taxidi.STATUS_CHECKED_IN:
                checked.remove(i)
            else:
                self.ResultsPanel.ResultsList.results[i]['status'] = taxidi.STATUS_CHECKED_IN
                self.ResultsPanel.ResultsList.UpdateStatus(i)
        
        #Return to main screen if there's nothing to do
        if len(checked) == 0:
            notify.info("Nothing selected", "Please select records which have not yet been checked-in to continue")
            return
        
        #Convert them to explicit database id references
        selected = [ self.ResultsPanel.ResultsList.results[i]['id'] for i in checked ]
        
        #Convert references into full data dictionary useable by check-in producer
        fullResults =  []
        for row in self.results:
            for i in selected:
                if i == row['id']:
                    fullResults.append(row)
                    
        #Convert references to activity and room into explicit dictionary/text
        for row in fullResults:
            row['activity'] = self.db.GetActivityById(row['activity']) #as dict
            row['room'] = self.db.GetRoomByID(row['room'])
                    
        #Perform check-in on database and printing.
        self.DoMultiCheckin((self.service['name'],), fullResults)
        
        #Close the result panel:
        self.ResultsPanelCancel(None)
        
    def DoMultiCheckin(self, services, data):
        #TODO: Debug this for sqlite backend
        self.multiJobID += 1
        #~ self._multiCheckinProducer(0, data, services)
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
            notify.error("Thread Error", "Result for job %s raised exception: %s" % (jobID, exc) )
            self.log.error("Thread Error: Result for job %s raised exception: %s" % (jobID, exc))
            print traceback.format_exc()
            self.log.error(traceback.format_exc())
            raise
            return
            
    def _multiCheckinProducer(self, jobID, data, services):
        #Note: activity is a dictionary
        #Note: dictionary keys match database, not _checkinProducer()
        #Get secure code, if needed
        #self.activities = self.db.GetActivities()
        trash = []
        for row in data:
            import pprint
            pprint.pprint(data)
            pprint.pprint(row)
            
            #~ activity = self.activities[row['activity']-1]
            #~ room = self.db.GetRoomByID(row['room'])
            activity = row['activity']
            room = row['room']
            
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
                
            try:
                if args.location is not None:
                    location = args.location
                else:
                    location = conf.config['config']['name']
            except AttributeError:
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
        
    def OnMultiCheckinMultiService(self, event):
        #^ This needs a better method name
        
        #Get the selected items.
        checked = self.ResultsPanel.ResultsList.GetSelected() #Index of checked items
        copyofChecked = checked[:]
        
        #Remove those already marked as checked-in.
        for i in copyofChecked:
            if self.ResultsPanel.ResultsList.results[i]['status'] == taxidi.STATUS_CHECKED_IN:
                checked.remove(i)
            else:
                self.ResultsPanel.ResultsList.results[i]['status'] = taxidi.STATUS_CHECKED_IN
                self.ResultsPanel.ResultsList.UpdateStatus(i)
                
        #Stop if nothing's selected:
        if len(checked) == 0:
            notify.info("Nothing selected", "Please select records which have not yet been checked-in to continue")
            return
        
        #Convert them to explicit database id references
        selected = [ self.ResultsPanel.ResultsList.results[i]['id'] for i in checked ]
        
        #Convert references into full data dictionary useable by check-in producer
        fullResults =  []
        for row in self.results:
            for i in selected:
                if i == row['id']:
                    fullResults.append(row)
                    
         #Convert references to activity and room into explicit dictionary/text
        for row in fullResults:
            row['activity'] = self.db.GetActivityById(row['activity']) #as dict
            row['room'] = self.db.GetRoomByID(row['room'])
        
        #Prompt the user for services selection:
        self.services = self.db.GetServices()
        dlg = SearchResultsList.MultiServiceDialog(self.frame, wx.ID_ANY, self.services)
        if dlg.ShowModal() == wx.ID_OK:
            if dlg.selected != []: #Make sure something's selected
                #Selected services as list for use by check-in producer
                services = [ i['name'] for i in dlg.selected ]
                #print "services ", services
                
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
        
        #Close panel and return to search:
        self.ResultsPanelCancel(None)
        
    def ResetSearchColour(self, event):
        self.SearchPanel.Search.SetBackgroundColour(wx.NullColour)
        
    def OnSearch(self, event):
        
        #Get input:
        query = self.SearchPanel.Search.GetValue()
        if query == '':
            self.SearchPanel.Search.SetBackgroundColour('pink')
            self.SearchPanel.Search.SetFocus()
            return
        
        #Do search:
        results = self.db.Search(query)
        if len(results) == 1:
            #Show single record
            self.SearchPanel.Hide()
            self.ActionPanel.Show()
            self.SetRecordData(results[0])
            # Show birthday notice
            #~ if results[0]['dob'][5:] == date.today().isoformat()[5:]:
                #~ self.BirthdayPanel.Show()
            
        elif len(results) > 1:
            #Show multiple results:
            self.SearchPanel.Hide()
            self.ResultsPanel.Show()
            #Remember the query:
            self.results = results
            self.ResultsPanel.results = self.FormatResults(results)
            self.ResultsPanel.ResultsList.ShowResults(self.ResultsPanel.results)
            #~ birthday = False
            #~ for i in results:
                #~ if date.today().isoformat()[5:] in i['dob'][5:]:
                    #~ birthday = True
            #~ if birthday:
                #~ self.BirthdayPanel.Show()
            
        else: #No results
            self.SearchPanel.Search.SetValue('')
            self.SearchPanel.Search.SetFocus()
            self.SearchPanel.Search.SetBackgroundColour("red")
            #~ notify.error("No Results", "No search results for {0}".format(query))
            notify.warning("No Results", "No search results for {0}".format(query))
            return
            
        #Close OSK keyboard (onboard)
        subprocess.Popen(('/usr/bin/pkill', 'onboard'))
        
    def SetMissingData(self):
        self.ActionPanel.CheckinButton.Disable()
        return
        
        
    def SetRecordData(self, data):
        name = "{0} {1}".format(data['name'], data['lastname'])
        if data['dob'] == '' or data['dob'] == None:
          #Show missing data dialogue
          self.SetMissingData()
          #return
        
        #Get photo path
        #print data['picture']
        if data['picture'] != None and data['picture'] != '':
            try: #Load photo if the path exists.
                photo = self.PhotoStorage.getThumbnailPath(data['picture'])
                f = open(photo)
                f.close()
            except IOError: #Otherwise, don't use one.
                photo = None
        else:
            photo = None
        status = self.db.GetStatus(data['id'], True)
        if data['visitor']:
            rType = "Visitor"
        else:
            rType = "Member"
        if status['status'] == taxidi.STATUS_NONE:
            self.ActionPanel.CheckinButton.SetLabel('Check-in') #TODO binding
            statusText = rType
        elif status['status'] == taxidi.STATUS_CHECKED_IN:
            if type(status['checkin']) in (str, unicode):
                checkin = datetime.datetime.strftime(datetime.datetime.strptime(str(status['checkin']), "%Y-%m-%dT%H:%M:%S"), "%H:%M:%S")
            elif type(status['checkin']) is datetime.datetime:
                checkin = datetime.datetime.strftime(status['checkin'], "%H:%M:%S")
            else:
                checkin = "???" #Invalid status
            statusText = "{0} - Checked-in at {1}".format(rType, checkin)
            self.ActionPanel.CheckinButton.SetLabel('Check-out') #TODO binding
        elif status['status'] == taxidi.STATUS_CHECKED_OUT:
            if type(status['checkout']) is str:
                checkout = datetime.datetime.strftime(datetime.datetime.strptime(str(status['checkout']), "%Y-%m-%dT%H:%M:%S"), "%H:%M:%S")
            elif type(status['checkout']) is datetime.datetime:
                checkout = datetime.datetime.strftime(status['checkout'], "%H:%M:%S")
            statusText = "{0} - Checked-out at {1}".format(rType, checkout)
            self.ActionPanel.CheckinButton.SetLabel('Check-in') #TODO binding
            
        #Check if record is past expiration, if so then check-out.        
        
        self.ActionPanel.SetData(name, data['phone'], 
                                 self.activities[data['activity']-1]['name'],
                                 self.db.GetRoomByID(data['room']),
                                 statusText, photo)
                                 
        self.ActionPanel.data = data #Remember loaded data
                                 
    def FormatResults(self, results):
        """
        Formats a results dictionary for displaying on the results panel.
        Joins with activity name, room name, and check-in status.
        """
        ret = []
        activities = [ i['name'] for i in self.db.GetActivities() ]
        #~ rooms = { i['id'] : i['name'] for i in self.db.GetRooms() }
        #Fixed for python 2.6. (Dict comprehensions only >= 2.7)
        rooms = dict( (i['id'], i['name']) for i in self.db.GetRooms() )
        for i in results:
            room = ''
            if i['room'] != None:
                if int(i['room']) > len(rooms): #Room reference is invalid:
                    i['room'] = 0
            if i['room'] == None or i['room'] == 0:
                room = u'—'
            else:
                room = rooms[int(i['room'])]
            if int(i['activity'])-1 > len(activities): #activity/room index starts at 0
                i['activity'] = 0
            #Get status:
            status = self.db.GetStatus(i['id'], True)
            if status['status'] == taxidi.STATUS_CHECKED_OUT:
                checkout = status['checkout']
            else:
                checkout = None
            ret.append({ 'id': i['id'], 'name': ('%s %s' % (i['name'], i['lastname'])),
                         'activity': activities[int(i['activity'])-1],
                         'room': room, 'status': status['status'],
                         'checkout-time': checkout, 'code': status['code'],
                         'picture': str(i['picture']) })
        return ret

    def BirthdayPanelClose(self, event):
        self.BirthdayPanel.Hide()
        
    def ActionPanelCancel(self, event):
        """
        Event callback from closing the ActionPanel (single result).
        """
        self.ActionPanel.Hide()
        self.SearchPanel.Show()
        self.SearchPanel.Search.SetValue('') #Clear the search entry
        self.SearchPanel.Search.SetFocus()
        
    def ResultsPanelCancel(self, event):
        """
        Event callback from closing ResultsPanel (multiple results).
        """
        self.ResultsPanel.Hide()
        self.SearchPanel.Show()
        self.SearchPanel.Search.SetValue('') #Clear the search entry
        self.SearchPanel.Search.SetFocus()
        self.ResultsPanel.ResultsList.DeleteAllItems() #Clear results
        
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
        
    def _on_size(self, event):
        event.Skip()
        #Resize the panels to trigger their resize event:
        size = self.frame.GetSize()
        self.SearchPanel.SetSize((1024, 768))
        self.SearchPanel.CentreOnParent(dir=wx.HORIZONTAL)
        self.ActionPanel.SetSize((1024, 768))
        self.ActionPanel.CentreOnParent(dir=wx.HORIZONTAL)
        self.ResultsPanel.SetSize((1024, 768))
        self.ResultsPanel.CentreOnParent(dir=wx.HORIZONTAL)
        self.BirthdayPanel.SetSize((1024, 768))
        self.BirthdayPanel.CentreOnParent(dir=wx.HORIZONTAL)
        
        
if __name__ == "__main__":     
    app = KioskApp()
    app.MainLoop()
