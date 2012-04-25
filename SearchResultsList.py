#!/usr/bin/env python
#-*- coding:utf-8 -*-

# 2012-04-23: Initial work.
# 2012-04-25: Fixed bug in ultimatelistctrl with background colour.

#TODO: Display 'status' column.

import wx
try:
    from ulc import ultimatelistctrl as ULC
except ImportError:
    from wx.lib.agw import ultimatelistctrl as ULC
import taxidi

LIST_AUTOSIZE_FILL = -3

########################################################################
class SearchResultsPanel(wx.Panel):
    """
    Shows search results in a list based on UltimateListCtrl.
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
        self.ultimateList.InsertColumnInfo(2, info)

        self.SetFont(self.boldfont)
        self.checkboxes = []

        self.ultimateList.SetColumnWidth(0, 60)
        #~ self.ultimateList.SetColumnWidth(1, 350)
        self.ultimateList.SetColumnWidth(1, LIST_AUTOSIZE_FILL)
        self.ultimateList.SetColumnWidth(2, 160)
        self.ultimateList.SetColumnWidth(3, 160)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ultimateList, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Bind(ULC.EVT_LIST_ITEM_SELECTED, self.Click, self.ultimateList)

    def Click(self, event):
        print self.ultimateList.GetFirstSelected()

    def ButtonPress(self, event):
        i = event.GetEventObject().id
        if self.checkboxes[i].GetValue() == True: #Toggled on
            self.checkboxes[i].SetLabel(u'✔')
            self.checkboxes[i].SetForegroundColour('#61BD36')
        else: #Toggled off
            self.checkboxes[i].SetLabel('')

    def DeleteAllItems(self):
        """Deletes all entries currently in the list"""
        #BUG: for some reason, UltimateListCtrl.DeleteAllItems() has troubles.
        #  So we'll do deletion manually.
        items = self.ultimateList.GetItemCount()
        for i in reversed(range(items)):
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
        for i in range(len(results)):
            pos = self.ultimateList.InsertStringItem(i, '')
            self.ultimateList.SetStringItem(pos, 1, results[i]['name'])
            self.ultimateList.SetStringItem(pos, 2, results[i]['activity'])
            self.ultimateList.SetStringItem(pos, 3, results[i]['room'])

            #Set the name column to bold:
            item = self.ultimateList.GetItem(i, 1)
            item.SetMask(ULC.ULC_MASK_FONT)
            item.SetFont(self.boldfont)
            self.ultimateList.SetItem(item)

            self.checkboxes.append(wx.ToggleButton(self.ultimateList, id=i,
                label="", size=(50, 50)))
            self.Bind(wx.wx.EVT_TOGGLEBUTTON, self.ButtonPress,
                self.checkboxes[i])
            self.checkboxes[i].id = i
            self.checkboxes[i].SetFont(self.checkfont)

            self.ultimateList.SetItemWindow(pos, col=0, wnd=self.checkboxes[i],
                expand=False)

            if i % 2 == 1: #Make every other row a light grey for legibility.
                self.ultimateList.SetItemBackgroundColour(i, wx.Colour(220, 220, 220))
            #Note: Due to a bug in ultimatelistctrl, coloured backgrounds with
            # a font in this way only works with the included version of
            # ultimatelistctrl.
            self.ultimateList.SetItemFont(i, self.font)


########################################################################
class TestFrame(wx.Frame):
    """"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        wx.Frame.__init__(self, None, title="UltimateListCtrl test", size=(1024, 558))
        panel = SearchResultsPanel(self)
        panel.ShowResults(results)
        self.Show()

#----------------------------------------------------------------------
if __name__ == "__main__":
    results = [ {'name':'Johnathan Churchgoer', 'activity':'Explorers',  'room':'Jungle Room', 'status':taxidi.STATUS_NONE},
                {'name':'Jane Smith',           'activity':'Explorers',  'room':'Ocean Room',  'status':taxidi.STATUS_CHECKED_IN},
                {'name':'Joseph Flint',         'activity':'Outfitters', 'room':u'—',          'status':taxidi.STATUS_CHECKED_OUT} ]
    app = wx.App(False)
    frame = TestFrame()
    app.MainLoop()
