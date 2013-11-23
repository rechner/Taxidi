#!/usr/bin/env python
#-*- coding:utf-8 -*-

# 2012-04-23: Initial work.
# 2012-04-25: Fixed bug in ultimatelistctrl with background colour.

#TODO: Create left-handed search results panel (SearchResultsList.py)

import wx
import  wx.lib.newevent
import time
import datetime
from datetime import date

try:
    from ulc import ultimatelistctrl as ULC
except ImportError:
    from wx.lib.agw import ultimatelistctrl as ULC
import taxidi

LIST_AUTOSIZE_FILL = -3

#Some events for internal handling:
t_RESULT_LIST_CHECK = wx.NewEventType()
RESULT_LIST_CHECK = wx.PyEventBinder(t_RESULT_LIST_CHECK, 1)
CheckOutEvent, EVT_CHECKOUT = wx.lib.newevent.NewEvent()
CheckOutCommandEvent, EVT_CHECKOUT_COMMAND = wx.lib.newevent.NewCommandEvent()

########################################################################
class SearchResultsPanel(wx.Panel):
    """
    Shows search results in a list based on UltimateListCtrl.
    """

    #----------------------------------------------------------------------
    def __init__(self, parent, size=None):
        """Constructor"""
        wx.Panel.__init__(self, parent)
        
        if size != None:
            self.SetSize(size)
            self.Layout()

        self.font = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self.font.SetPointSize(16)
        self.boldfont = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self.boldfont.SetWeight(wx.BOLD)
        self.boldfont.SetPointSize(16)
        self.checkfont = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self.checkfont.SetWeight(wx.BOLD)
        self.checkfont.SetPointSize(28)

        self.ultimateList = ULC.UltimateListCtrl(self, agwStyle = ULC.ULC_REPORT
                                            | ULC.ULC_HAS_VARIABLE_ROW_HEIGHT
                                            | ULC.ULC_HRULES)

        info = ULC.UltimateListItem()
        info._format = wx.LIST_FORMAT_CENTRE
        info._mask = wx.LIST_MASK_TEXT |  wx.LIST_MASK_FORMAT | ULC.ULC_MASK_FONT
        info._image = []
        info._text = u'✔'
        info._font = self.boldfont
        self.ultimateList.InsertColumnInfo(0, info)

        info = ULC.UltimateListItem()
        info._mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT | ULC.ULC_MASK_FONT
        info._format = 0
        info._text = 'Name'
        info._font = self.boldfont
        info._image = []
        self.ultimateList.InsertColumnInfo(1, info)

        info = ULC.UltimateListItem()
        info._mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT | ULC.ULC_MASK_FONT
        info._format = ULC.ULC_FORMAT_CENTRE
        info._text = 'Activity'
        info._font = self.boldfont
        info._image = []
        self.ultimateList.InsertColumnInfo(2, info)

        info = ULC.UltimateListItem()
        #wx.LIST_MASK_IMAGE
        info._mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT | ULC.ULC_MASK_FONT
        info._format = ULC.ULC_FORMAT_CENTRE
        info._text = 'Room'
        info._font = self.boldfont
        info._image = []
        self.ultimateList.InsertColumnInfo(3, info)

        info = ULC.UltimateListItem()
        info._mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT | ULC.ULC_MASK_FONT
        info._format = ULC.ULC_FORMAT_CENTRE
        info._text = 'Status'
        info._font = self.boldfont
        info._image = []
        self.ultimateList.InsertColumnInfo(4, info)

        self.SetFont(self.boldfont)
        self.checkboxes = []

        self.ultimateList.SetColumnWidth(0, 60)
        #~ self.ultimateList.SetColumnWidth(1, 350)
        self.ultimateList.SetColumnWidth(1, LIST_AUTOSIZE_FILL)
        self.ultimateList.SetColumnWidth(2, 180)
        self.ultimateList.SetColumnWidth(3, 180)
        self.ultimateList.SetColumnWidth(4, 160)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ultimateList, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Bind(ULC.EVT_LIST_ITEM_SELECTED, self.Click, self.ultimateList)

        self

    def Click(self, event):
        #TODO: external event triggering.  (Pub/sub?)
        #~ print self.ultimateList.GetFirstSelected()
        pass

    def ButtonPress(self, event):
        i = event.GetEventObject().id
        if self.checkboxes[i].GetValue() == True: #Toggled on
            self.checkboxes[i].SetLabel(u'✔')
            self.checkboxes[i].SetForegroundColour('#61BD36')
        else: #Toggled off
            if self.results[i]['status'] == taxidi.STATUS_CHECKED_IN:
                self.checkboxes[i].SetLabel(u'✘')
                self.checkboxes[i].SetForegroundColour('#d42b1d') #replace with themeCheckOffColour
                #TODO: Read database and see if checkout action required for activity.
                #TODO: Read config and see if check-out action is allowed at this station (disallow for kiosk)
                #TODO: Display authorized/unauthorized guardians if needed.
                evt = CheckOutEvent(data = self.results[i])
                evt.SetEventObject(self.checkboxes[i])
                wx.PostEvent(self.GetEventHandler(), evt)
                #Change check-in status:
                #~ self.results[i]['status'] = taxidi.STATUS_CHECKED_OUT
                #~ self.results[i]['checkout-time'] = datetime.datetime.now().strftime("%H:%M:%S")
                #~ self.UpdateStatus(i)
            elif self.results[i]['status'] == taxidi.STATUS_CHECKED_OUT:
                #Set checkbox back to x (checked-out) and don't perform an action.
                self.checkboxes[i].SetLabel(u'✘')
                self.checkboxes[i].SetForegroundColour('#d42b1d') #replace with themeCheckOffColour
                #Send event
                #~ self.GetEventHandler().ProcessEvent(EVT_CHECKOUT)
            else:
                #Just unset the label:
                self.checkboxes[i].SetLabel('')
        #Send event:
        evt2 = wx.PyCommandEvent(t_RESULT_LIST_CHECK, self.GetId())
        self.GetEventHandler().ProcessEvent(evt2)
        event.Skip()

    def SetToggle(self, id, value):
        self.checkboxes[id].SetValue(value)
        if self.checkboxes[id].GetValue() == True:
            self.checkboxes[id].SetLabel(u'✔')
            self.checkboxes[id].SetForegroundColour('#61BD36')
        else: #Toggled off
            self.checkboxes[id].SetLabel('')

    def DeleteAllItems(self):
        """Deletes all entries currently in the list"""
        #FIXME: for some reason, UltimateListCtrl.DeleteAllItems() has troubles.
        #  So we'll do deletion manually.  UPDATE: I left this code for a few
        #  hours and suddenly it broke.  Work around is in place in
        #  ultimatelistctrl.py
        items = self.ultimateList.GetItemCount()
        for i in reversed(xrange(items)):
            self.ultimateList.DeleteItem(i)
        del self.checkboxes
        self.checkboxes = []

    def GetSelected(self):
        """Returns a list of the checked items"""
        result = []
        for i in range(len(self.checkboxes)):
            if self.checkboxes[i].GetValue() == True:
                result.append(i)
        return result

    def InsertItem(self, item):
        pass

    def UpdateStatus(self, i):
        if self.results[i]['status'] == taxidi.STATUS_CHECKED_IN:
            self.ultimateList.SetStringItem(i, 4, 'Checked-in')
            self.SetCellTextColour(i, 4, '#2F6617')
        elif self.results[i]['status'] == taxidi.STATUS_CHECKED_OUT:
            print type(self.results[i]['checkout-time'])
            if isinstance(self.results[i]['checkout-time'], datetime.datetime):
                self.results[i]['checkout-time'] = \
                    datetime.datetime.strftime(self.results[i]['checkout-time'], "%X")
            self.ultimateList.SetStringItem(i, 4,
                'Checked-out\n%s' % self.results[i]['checkout-time'])
            self.SetCellTextColour(i, 4, wx.RED)

    def ShowResults(self, results):
        """
        Clears and populates the list with data from a dictionary..
        Each entry requires the following keys:
            'name'
            'activity'
            'room'
            'status'
        Where 'status' can be any of the following:
            taxidi.STATUS_NONE | taxidi.STATUS_CHECKED_IN | taxidi.STATUS_CHECKED_OUT
        """

        self.DeleteAllItems()
        self.results = results
        for i in range(len(results)):
            pos = self.ultimateList.InsertStringItem(i, '')
            self.ultimateList.SetStringItem(pos, 1, results[i]['name'])
            self.ultimateList.SetStringItem(pos, 2, results[i]['activity'])
            self.ultimateList.SetStringItem(pos, 3, results[i]['room'])

            #Set the name column to bold:
            self.SetCellFont(i, 1, self.boldfont)

            self.checkboxes.append(wx.ToggleButton(self.ultimateList, id=i,
                label="", size=(50, 50)))
            self.Bind(wx.EVT_TOGGLEBUTTON, self.ButtonPress,
                self.checkboxes[i])
            self.checkboxes[i].id = i
            self.checkboxes[i].SetFont(self.checkfont)

            self.ultimateList.SetItemWindow(pos, col=0, wnd=self.checkboxes[i],
                expand=False)

            if results[i]['status'] == taxidi.STATUS_CHECKED_IN:
                self.ultimateList.SetStringItem(pos, 4, 'Checked-in')
                self.SetCellTextColour(pos, 4, '#2F6617')
                self.SetToggle(i, True)
            elif results[i]['status'] == taxidi.STATUS_CHECKED_OUT:
                if isinstance(self.results[i]['checkout-time'], datetime.datetime):
                    self.results[i]['checkout-time'] = \
                        datetime.datetime.strftime(self.results[i]['checkout-time'], "%X")
                elif type(self.results[i]['checkout-time'])  in (str, unicode):
                    self.results[i]['checkout-time'] = \
                        datetime.datetime.strftime(datetime.datetime.strptime( \
                        str(self.results[i]['checkout-time']), \
                        "%Y-%m-%dT%H:%M:%S"), "%X")
                self.ultimateList.SetStringItem(pos, 4,
                    'Checked-out\n%s' % results[i]['checkout-time'])
                self.SetCellTextColour(pos, 4, wx.RED)
                self.checkboxes[i].SetLabel(u'✘')
                self.checkboxes[i].SetForegroundColour('#d42b1d') #replace with themeCheckOffColour

            if i % 2 == 1: #Make every other row a light grey for legibility.
                colour = self.hex_to_rgb('#DCDCDC')
                self.ultimateList.SetItemBackgroundColour(i, wx.Colour(colour[0], colour[1], colour[2]))
            #Note: Due to a bug in ultimatelistctrl, coloured backgrounds with
            # a font in this way only works with the included version of
            # ultimatelistctrl.  The local version has a few work-arounds.
            self.ultimateList.SetItemFont(i, self.font)

    def SetCellFont(self, row, col, font, colour=None):
        """
        Sets an individual cell's font [and optionally colour].

        :param `row`: The item's identifying row.
        :param `col`: The item's identifying column.
        :param `font`: A valid wx.Font to apply.
        :param `colour`: (opt.) A valid wx.Colour to apply.
        """
        item = self.ultimateList.GetItem(row, col)
        if colour:
            item.SetMask(ULC.ULC_MASK_FONT | ULC.ULC_MASK_FONTCOLOUR)
            item.SetTextColour(colour)
        else:
            item.SetMask(ULC.ULC_MASK_FONT)
        item.SetFont(font)
        self.ultimateList.SetItem(item)

    def SetCellTextColour(self, row, col, colour):
        """
        Sets an individual cell's text colour.
        """
        item = self.ultimateList.GetItem(row, col)
        item.SetMask(ULC.ULC_MASK_FONTCOLOUR)
        item.SetTextColour(colour)
        #item.SetFont(item.GetFont())
        self.ultimateList.SetItem(item)

    def hex_to_rgb(self, value):
        """
        Converts an HTML hex colour to (r,g,b).
        For some reason some parts of ULC require an wx.Colour object.
        """
        value = value.lstrip('#')
        lv = len(value)
        return tuple(int(value[i:i+lv/3], 16) for i in range(0, lv, lv/3))


class MultiServicePanel(wx.Panel):
    """
    UltimateListCtrl based list for selecting multiple services to check-in to.
    """

    #----------------------------------------------------------------------
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent)

        self.font = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self.font.SetPointSize(16)
        self.boldfont = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self.boldfont.SetWeight(wx.BOLD)
        self.boldfont.SetPointSize(16)
        self.checkfont = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self.checkfont.SetWeight(wx.BOLD)
        self.checkfont.SetPointSize(28)

        self.ultimateList = ULC.UltimateListCtrl(self, agwStyle = ULC.ULC_REPORT
                                            | ULC.ULC_HAS_VARIABLE_ROW_HEIGHT
                                            | ULC.ULC_HRULES)

        info = ULC.UltimateListItem()
        info._format = wx.LIST_FORMAT_CENTRE
        info._mask = wx.LIST_MASK_TEXT |  wx.LIST_MASK_FORMAT | ULC.ULC_MASK_FONT
        info._image = []
        info._text = u'✔'
        info._font = self.boldfont
        self.ultimateList.InsertColumnInfo(0, info)

        info = ULC.UltimateListItem()
        info._mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT | ULC.ULC_MASK_FONT
        info._format = 0
        info._text = 'Service'
        info._font = self.boldfont
        info._image = []
        self.ultimateList.InsertColumnInfo(1, info)

        self.SetFont(self.boldfont)
        self.checkboxes = []

        self.ultimateList.SetColumnWidth(0, 60)
        #~ self.ultimateList.SetColumnWidth(1, 350)
        self.ultimateList.SetColumnWidth(1, LIST_AUTOSIZE_FILL)

        sz = wx.BoxSizer(wx.HORIZONTAL)
        st = wx.StaticText(self, wx.ID_ANY, 'Select services, then press "OK"', wx.DefaultPosition, wx.DefaultSize, 0)
        self.AcceptButton = wx.Button(self, wx.ID_OK, size=(160, -1))
        self.CancelButton = wx.Button(self, wx.ID_CANCEL, size=(160, -1))
        
        sz.Add(st, 1, wx.ALL, 5)
        sz.AddStretchSpacer()
        sz.Add(self.CancelButton, 1, wx.EXPAND | wx.ALL, 5)
        sz.Add(self.AcceptButton, 1, wx.EXPAND | wx.ALL, 5)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sz, 1, wx.ALL | wx.EXPAND, 5)
        sizer.Add(self.ultimateList, 6, wx.EXPAND)
        self.SetSizer(sizer)
        self.Bind(ULC.EVT_LIST_ITEM_SELECTED, self.Click, self.ultimateList)

    def Click(self, event):
        pass

    def ButtonPress(self, event):
        i = event.GetEventObject().id
        if self.checkboxes[i].GetValue() == True: #Toggled on
            self.checkboxes[i].SetLabel(u'✔')
            self.checkboxes[i].SetForegroundColour('#61BD36')
        else: #Toggled off
            self.checkboxes[i].SetLabel('')


    def SetToggle(self, id, value):
        self.checkboxes[id].SetValue(value)
        if self.checkboxes[id].GetValue() == True:
            self.checkboxes[id].SetLabel(u'✔')
            self.checkboxes[id].SetForegroundColour('#61BD36')
        else: #Toggled off
            self.checkboxes[id].SetLabel('')

    def DeleteAllItems(self):
        """Deletes all entries currently in the list"""
        #FIXME: for some reason, UltimateListCtrl.DeleteAllItems() has troubles.
        #  So we'll do deletion manually.  UPDATE: I left this code for a few
        #  hours and suddenly it broke.  Work around is in place in
        #  ultimatelistctrl.py
        items = self.ultimateList.GetItemCount()
        for i in reversed(xrange(items)):
            self.ultimateList.DeleteItem(i)
        del self.checkboxes
        self.checkboxes = []

    def GetSelected(self):
        """Returns a list of the checked items"""
        result = []
        for i in range(len(self.checkboxes)):
            if self.checkboxes[i].GetValue() == True:
                result.append(self.items[i])
        return result

    def SetServices(self, services, filter=False, force=False, hide=False):
        """
        Clears and populates the list data from a `services` dictionary.
        `filter`: When True, the services attributes will be filtered based on
            attributes, e.g. only days matching Sunday will be shown on Sunday.
            Services whose endTime has passed will be grey, but still available
            for selection. Services which are active are marked green and selected
            by default.
        `force`: When true, services whose endTime has passed will be disabled from
            selection.
        `hide`: When true, services whose endTime has passed will not be shown.
        """

        self.items = []
        self.DeleteAllItems()
        self.services = services
        today = date.today()
        now = time.strftime('%H:%M:%S', time.localtime())
        a = 0
        for i in range(len(services)):
            #Filter is True and rough check that times are set for the service.
            if filter:
                if services[i]['day'] == date.isoweekday(today) or services[i]['day'] == 0:
                    #Show if day of week matches today's:
                    self.FormatItem(services[i], a)

                    delta = datetime.datetime.strptime(str(services[i]['endTime']), '%H:%M:%S') - \
                            datetime.datetime.strptime(now, '%H:%M:%S')
                    if delta.days < 0:  #Service has ended
                        self.SetCellTextColour(a, 1, 'grey')
                        if force: self.checkboxes[i].Disable()

                    if services[i]['time'] == '': #Assume All day
                        delta2 = datetime.datetime.strptime('00:00:00', '%H:%M:%S') - datetime.datetime.strptime(now, '%H:%M:%S')
                    else:
                        delta2 = datetime.datetime.strptime(str(services[i]['time']), '%H:%M:%S') - datetime.datetime.strptime(now, '%H:%M:%S')
                    if delta.days == 0 and delta2.days < 0:
                        self.SetCellTextColour(a, 1, 'darkgreen')
                        self.SetToggle(a, True)

                    a += 1 #incrament the list counter
                    self.items.append(services[i]) #List of services that are displayed
                else:
                    pass #Don't add it to the list
            elif not filter:
                self.FormatItem(services[i], a)
                a += 1

    def FormatItem(self, service, i):
        pos = self.ultimateList.InsertStringItem(i, '')
        self.ultimateList.SetStringItem(pos, 1, service['name'])

        #Set the name column to bold:
        self.SetCellFont(i, 1, self.boldfont)

        self.checkboxes.append(wx.ToggleButton(self.ultimateList, id=i,
            label="", size=(50, 50)))
        self.Bind(wx.wx.EVT_TOGGLEBUTTON, self.ButtonPress,
            self.checkboxes[i])
        self.checkboxes[i].id = i
        self.checkboxes[i].SetFont(self.checkfont)

        self.ultimateList.SetItemWindow(pos, col=0, wnd=self.checkboxes[i],
            expand=False)

        if i % 2 == 1: #Make every other row a light grey for legibility.
            colour = self.hex_to_rgb('#DCDCDC')
            self.ultimateList.SetItemBackgroundColour(i, wx.Colour(colour[0], colour[1], colour[2]))

    def GetItems(self):
        return self.items


    def SetCellFont(self, row, col, font, colour=None):
        """
        Sets an individual cell's font [and optionally colour].

        :param `row`: The item's identifying row.
        :param `col`: The item's identifying column.
        :param `font`: A valid wx.Font to apply.
        :param `colour`: (opt.) A valid wx.Colour to apply.
        """
        item = self.ultimateList.GetItem(row, col)
        if colour:
            item.SetMask(ULC.ULC_MASK_FONT | ULC.ULC_MASK_FONTCOLOUR)
            item.SetTextColour(colour)
        else:
            item.SetMask(ULC.ULC_MASK_FONT)
        item.SetFont(font)
        self.ultimateList.SetItem(item)

    def SetCellTextColour(self, row, col, colour):
        """
        Sets an individual cell's text colour.
        """
        item = self.ultimateList.GetItem(row, col)
        item.SetMask(ULC.ULC_MASK_FONTCOLOUR)
        item.SetTextColour(colour)
        #item.SetFont(item.GetFont())
        self.ultimateList.SetItem(item)

    def hex_to_rgb(self, value):
        """
        Converts an HTML hex colour to (r,g,b).
        For some reason some parts of ULC require an wx.Colour object.
        """
        value = value.lstrip('#')
        lv = len(value)
        return tuple(int(value[i:i+lv/3], 16) for i in range(0, lv, lv/3))

class MultiServiceDialog(wx.Dialog):
    def __init__(self, parent, id, services):
        """Constructor"""
        wx.Dialog.__init__(self, parent, id, size=(800, 500))
        self.InitUI()
        if services != None:
            self.SetServices(services)
        
    def InitUI(self):
        self.panel = MultiServicePanel(self)
        self.panel.CancelButton.Bind(wx.EVT_BUTTON, self.Cancel)
        self.panel.AcceptButton.Bind(wx.EVT_BUTTON, self.Accept)
        
    def SetServices(self, services):
        self.panel.SetServices(services, filter=True)
    
    def Accept(self, event):
        self.selected = self.panel.GetSelected()
        self.EndModal(wx.ID_OK)
    
    def Cancel(self, event):
        self.EndModal(wx.ID_CANCEL)
        self.Close()
        
        

########################################################################
class TestFrame(wx.Frame):
    """"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        #~ wx.Frame.__init__(self, None, title="UltimateListCtrl test", size=(1024, 558))
        
        #~ wx.Frame.__init__(self, None, title="UltimateListCtrl test", size=(500, 400))
        #~ panel = SearchResultsPanel(self)
        #~ panel.ShowResults(results)
        
        #~ panel = MultiServicePanel(self)
        #~ self.Show()
        
        #~ from dblib import sqlite as database
        #~ db = database.Database("~/.taxidi/database/users.db")
        #~ panel.SetServices(db.GetServices(), True)
        #~ panel.SetServices([ {'id': 1,  'name': 'First Service', 'day': 2, 'time': '00:00:00', 'endTime': '00:09:00'},
                             #~ {'id': 2, 'name': 'Second Service', 'day': 2, 'time': '00:30:00', 'endTime': '00:45:00'},
                             #~ {'id': 3, 'name': 'Third Service', 'day': 0, 'time': '00:30:00', 'endTime': '01:59:59'},
                             #~ {'id': 4, 'name': 'Every day', 'day': 0, 'time': '00:00:00', 'endTime': '17:53:59'} ], True)
        #~ print panel.GetSelected()
        


#----------------------------------------------------------------------
if __name__ == "__main__":
    #~ results = [ {'name':'Johnathan Churchgoer', 'activity':'Explorers',  'room':'Jungle Room', 'status':taxidi.STATUS_CHECKED_IN},
                #~ {'name':'Jane Smith',           'activity':'Explorers',  'room':'Ocean Room',  'status':taxidi.STATUS_CHECKED_IN},
                #~ {'name':'Jane Smith',           'activity':'Explorers',  'room':'Ocean Room',  'status':taxidi.STATUS_NONE},
                #~ {'name':'Jane Smith',           'activity':'Explorers',  'room':'Ocean Room',  'status':taxidi.STATUS_NONE},
                #~ {'name':'Jane Smith',           'activity':'Explorers',  'room':'Ocean Room',  'status':taxidi.STATUS_NONE},
                #~ {'name':'Joseph Flint',         'activity':'Outfitters', 'room':u'—',          'status':taxidi.STATUS_CHECKED_OUT, 'checkout-time':'11:46:34'} ]
    app = wx.App(False)
    
    services = [ {'id': 1,  'name': 'First Service', 'day': 2, 'time': '00:00:00', 'endTime': '00:09:00'},
                             {'id': 2, 'name': 'Second Service', 'day': 2, 'time': '00:30:00', 'endTime': '00:45:00'},
                             {'id': 3, 'name': 'Third Service', 'day': 0, 'time': '00:30:00', 'endTime': '01:59:59'},
                             {'id': 4, 'name': 'Every day', 'day': 0, 'time': '00:00:00', 'endTime': '17:53:59'} ]
    dlg = MultiServiceDialog(None, wx.ID_ANY, services)
    if dlg.ShowModal() == wx.ID_OK:
        print dlg.selected
        print [ i['name'] for i in dlg.selected ]
    dlg.Destroy()
    print "done"
    app.MainLoop()
