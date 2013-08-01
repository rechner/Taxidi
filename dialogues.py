#!/usr/bin/env python
#-*- coding:utf-8 -*-
#TODO: rewrite this with logging and make it pretty.

#FIXME: RCX incorrectly complains "Cannot load resources from file" despite loading them anyways. (?)
#FIXME: For some reason, after clicking add, the time inputs don't disable, despite "All Day"
    #being checked. (Priority: LOW)

import os
import wx
from wx import xrc
import wx.gizmos as gizmos
import wx.lib.masked as masked
import datetime

resourceCache = dict()

def insureWxApp():
    """Create an instance of PySimpleApp if there is no app already.
    This is required by wxPython before creating any GUI objects.
    """
    global _wxApp
    _wxApp = wx.GetApp()
    if not _wxApp:
        _wxApp = wx.PySimpleApp()
    return _wxApp


def loadXrc(filePath, reload=False):
    """Return an xrc.XmlResource instance."""
    filePath = os.path.abspath(filePath)
    if reload or (filePath not in resourceCache):
        result = xrc.XmlResource(filePath)
        resourceCache[filePath] = result
    else:
        result = resourceCache[filePath]
    return result


def escapeSuppressor(evt):
    """wx.EVT_CHAR_HOOK handler that suppresses processing ESC.
    By default, if you don't have a Cancel button, wx will trigger the
    OK button when you press ESC. Binding this to a dialog will deactivate
    the ESC key. We need this when there is no Cancel button.
    """
    evt.Skip(evt.GetKeyCode() != wx.WXK_ESCAPE)


def buildDialog(filePath, resourceName, mayCancel, **defaults):
    """Return a configured wx.Dialog.
    Assumes that the OK and Cancel buttons are named ID_OK & ID_CANCEL.
    """
    res = loadXrc(filePath)
    insureWxApp()
    dlg = res.LoadDialog(None, resourceName)
    assert isinstance(dlg, wx.Dialog)
    #dlg.Fit()
    fetchWidget = dlg.FindWindowByName
    bOk     = dlg.FindWindowByName('ID_OK')
    bCancel = dlg.FindWindowByName('ID_CANCEL')
    bOk.SetId(wx.ID_OK)
    bCancel.SetId(wx.ID_CANCEL)
    if not mayCancel:
        bCancel.Disable()
        bCancel.Hide()
    for name, value in defaults.items():
        dlg.FindWindowByName(name).SetValue(value)

    #setfocus to the first input element
    for name, value in defaults.items():
        dlg.FindWindowByName(name).SetFocus()
        break

    if not mayCancel:
        dlg.Bind(wx.EVT_CHAR_HOOK, escapeSuppressor)
    return dlg


def runDialog(dlg, mayCancel, *itemNames):
    """Run the specified dialog and return the values of the named items.
    Return None if the user cancels.
    """
    while True:
        if dlg.ShowModal() == wx.ID_OK:
            result = tuple((dlg.FindWindowByName(name).GetValue()
                            for name in itemNames))
            break
        elif mayCancel:
            result = None
            break
        else:
            wx.Bell()
    return result


def useTemporaryDialog(filePath, resourceName, mayCancel,
                       *itemNames, **defaults):
    """Create a dialog, run it, capture the results, destroy the dialog,
    and return the results.
    Return None if the user cancels.
    """
    dlg = buildDialog(filePath, resourceName, mayCancel, **defaults)
    try:
        result = runDialog(dlg, mayCancel, *itemNames)
    finally:
        dlg.Destroy()
    return result


# --- Sample Dialog ---
def askLogin(defaultUser='', defaultPassword='', mayCancel=True):
    """Return None if user cancels; otherwise (user, password) as unicode."""
    result = useTemporaryDialog(os.path.join('xrc', 'username.xrc'),
                                'UsernameDialog', mayCancel,
                                'username', 'password',
                                username=defaultUser,
                                password=defaultPassword)
    return result

def askPass(defaultUser='', defaultPassword='', mayCancel=True):
    """Return None if user cancels; otherwise (user, password) as unicode."""
    result = useTemporaryDialog(os.path.join('xrc', 'password.xrc'),
                                'PasswordDialog', mayCancel,
                                'password',
                                password=defaultPassword)
    if result:
        return result[0]
    return result


class EditServices(wx.Dialog):
    def __init__(self, parent, id, database):
        wx.Dialog.__init__(self, parent, id, 'Edit Services', size=(500,400))
        self.database = database
        self.deleted = []
        self.added = []
        self.InitUI()

    def SetServices(self, services):
        self.services = services

        #Set the items in the list:
        a = []
        for i in self.services:
            a.append(i['name'])
        self.elb.SetStrings(a)

    def GetServices(self):
        return self.services

    def GetDeletedItems(self):
        """
        Returns only the items which were deleted.
        """
        return self.deleted

    def InitUI(self):

        MasterFlexSizer = wx.FlexGridSizer(2, 2, 0, 0)
        MasterFlexSizer.AddGrowableCol(0)
        MasterFlexSizer.AddGrowableRow(0)
        MasterFlexSizer.SetFlexibleDirection(wx.BOTH)
        MasterFlexSizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)


        self.elb = gizmos.EditableListBox(self, -1, "Services")
        self.elb.GetUpButton().Hide()
        self.elb.GetDownButton().Hide()
        self.elb.GetListCtrl().Bind(wx.EVT_LIST_ITEM_SELECTED, self.SelectItem)

        #Set the icons:
        AddButtonIcon = wx.Image('resources/icons/list-add-16.png')
        self.AddButton = self.elb.GetNewButton()
        self.AddButton.SetBitmapLabel(AddButtonIcon.ConvertToBitmap())
        self.AddButton.Bind(wx.EVT_BUTTON, self.AddItem)
        DelButtonIcon = wx.Image('resources/icons/list-remove-16.png')
        self.DelButton = self.elb.GetDelButton()
        self.DelButton.SetBitmapLabel(DelButtonIcon.ConvertToBitmap())
        self.DelButton.Bind(wx.EVT_BUTTON, self.RemoveItem)
        EditButtonIcon = wx.Image('resources/icons/list-edit-16.png')
        self.EditButton = self.elb.GetEditButton()
        self.EditButton.SetBitmapLabel(EditButtonIcon.ConvertToBitmap())

        MasterFlexSizer.Add(self.elb, 1, wx.ALL | wx.EXPAND, 5)

        controlSizer = wx.BoxSizer(wx.VERTICAL)
        self.SelectedText = wx.StaticText(self, wx.ID_ANY, 'Select a service to edit', wx.DefaultPosition, wx.DefaultSize, 0 )
        self.SelectedText.Wrap(-1)
        self.SelectedText.SetFont(wx.Font(-1, -1, wx.NORMAL, wx.BOLD))
        controlSizer.Add(self.SelectedText, 0, wx.TOP|wx.LEFT, 8)

        daysSizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Days'), wx.VERTICAL)
        horizDaysSizer = wx.BoxSizer(wx.HORIZONTAL)

        vdaysizer1 = wx.BoxSizer(wx.VERTICAL)
        self.EveryDay = wx.RadioButton(self, label='Everyday')
        self.Monday = wx.RadioButton(self, label='Monday')
        self.Tuesday = wx.RadioButton(self, label='Tuesday')
        self.Wednesday = wx.RadioButton(self, label='Wednesday')
        vdaysizer1.Add(self.EveryDay, 0, wx.RIGHT|wx.LEFT)
        vdaysizer1.Add(self.Monday, 0, wx.RIGHT|wx.LEFT)
        vdaysizer1.Add(self.Tuesday, 0, wx.RIGHT|wx.LEFT)
        vdaysizer1.Add(self.Wednesday, 0, wx.RIGHT|wx.LEFT)
        horizDaysSizer.Add(vdaysizer1, wx.EXPAND, 5)

        vdaysizer2 = wx.BoxSizer(wx.VERTICAL)
        self.Thursday = wx.RadioButton(self, label='Thursday')
        self.Friday = wx.RadioButton(self, label='Friday')
        self.Saturday = wx.RadioButton(self, label='Saturday')
        self.Sunday = wx.RadioButton(self, label='Sunday')
        vdaysizer2.Add(self.Thursday, 0, wx.RIGHT|wx.LEFT)
        vdaysizer2.Add(self.Friday, 0, wx.RIGHT|wx.LEFT)
        vdaysizer2.Add(self.Saturday, 0, wx.RIGHT|wx.LEFT)
        vdaysizer2.Add(self.Sunday, 0, wx.RIGHT|wx.LEFT)
        horizDaysSizer.Add(vdaysizer2, wx.EXPAND, 5)

        daysSizer.Add(horizDaysSizer, 1, wx.EXPAND, 5)
        controlSizer.Add(daysSizer, 0, wx.EXPAND|wx.ALL, 5)

        self.EveryDay.Bind(wx.EVT_RADIOBUTTON, self.SetEveryDay)
        self.Monday.Bind(wx.EVT_RADIOBUTTON, self.SetMonday)
        self.Tuesday.Bind(wx.EVT_RADIOBUTTON, self.SetTuesday)
        self.Wednesday.Bind(wx.EVT_RADIOBUTTON, self.SetWednesday)
        self.Thursday.Bind(wx.EVT_RADIOBUTTON, self.SetThursday)
        self.Friday.Bind(wx.EVT_RADIOBUTTON, self.SetFriday)
        self.Saturday.Bind(wx.EVT_RADIOBUTTON, self.SetSaturday)
        self.Sunday.Bind(wx.EVT_RADIOBUTTON, self.SetSunday)

        #== timeSizer ==
        timeSizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Time'), wx.VERTICAL)
        gsizer = wx.GridSizer(3, 2, 0, 0)

        #=== StartTime input ===
        timebox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.StartTimeCheckBox = wx.CheckBox(self, -1, 'Start Time:', wx.DefaultPosition, wx.DefaultSize)
        self.StartTimeCheckBox.Bind(wx.EVT_CHECKBOX, self.SetStartTime)
        self.StartTime = masked.TimeCtrl(self, -1, name="Start Time", fmt24hr=True )
        h = self.StartTime.GetSize().height
        spin1 = wx.SpinButton( self, -1, wx.DefaultPosition, (-1,h), wx.SP_VERTICAL )
        self.StartTime.BindSpinButton( spin1 )
        timebox1.Add(self.StartTime, 0)
        timebox1.Add(spin1, 0)
        #Default states:
        self.StartTime.Disable()
        #=== End StartTime ===

        gsizer.Add(self.StartTimeCheckBox, 0, wx.ALIGN_CENTRE_VERTICAL | wx.LEFT, 5)

        gsizer.Add(timebox1, 0, wx.EXPAND|wx.ALL, 5)

        #=== EndTime input ===
        timebox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.EndTimeCheckBox = wx.CheckBox(self, -1, 'End Time:', wx.DefaultPosition, wx.DefaultSize)
        self.EndTimeCheckBox.Bind(wx.EVT_CHECKBOX, self.SetEndTime)
        self.EndTime = masked.TimeCtrl(self, -1, name="Start Time", fmt24hr=True )
        h = self.EndTime.GetSize().height
        spin2 = wx.SpinButton( self, -1, wx.DefaultPosition, (-1,h), wx.SP_VERTICAL )
        self.EndTime.BindSpinButton( spin2 )
        timebox2.Add(self.EndTime, 0)
        timebox2.Add(spin2, 0)
        #Default states:
        self.EndTime.Disable()
        #=== End EndTime ===

        gsizer.Add(self.EndTimeCheckBox, 0, wx.ALIGN_CENTRE_VERTICAL | wx.LEFT, 5)
        gsizer.Add(timebox2, 0, wx.EXPAND|wx.ALL, 5)

        timeSizer.Add(gsizer, 0, wx.EXPAND|wx.ALL, 5)
        controlSizer.Add(timeSizer,0, wx.EXPAND|wx.ALL, 5)

        self.AllDayCheckBox = wx.CheckBox(self, -1, 'All Day', wx.DefaultPosition, wx.DefaultSize)
        self.AllDayCheckBox.Bind(wx.EVT_CHECKBOX, self.SetAllDay)
        gsizer.Add(self.AllDayCheckBox,  0, wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        self.AllDayCheckBox.SetValue(True)
        #== End timeSizer ==

        controlSizer.AddStretchSpacer() #Spacer
        self.controls = controlSizer

        #== Button Sizer ==
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.Cancel = wx.Button(self, wx.ID_CANCEL)
        buttonSizer.Add(self.Cancel, 1, wx.ALL, 5)
        self.Cancel.Bind(wx.EVT_BUTTON, self.OnQuit)

        self.Okay = wx.Button(self, wx.ID_OK)
        buttonSizer.Add(self.Okay, 1, wx.ALL, 5)
        self.Okay.Bind(wx.EVT_BUTTON, self.OnSave)

        controlSizer.Add(buttonSizer, 1, wx.ALIGN_RIGHT | wx.EXPAND, 5)
        #== End Button Sizer ==

        MasterFlexSizer.Add(controlSizer, 1, wx.RIGHT|wx.LEFT|wx.EXPAND, 5)

        self.SetSizer(MasterFlexSizer)
        self.Layout()

        self.DisableOptions()

    def DisableOptions(self):
        #Disable everything (e.g. nothing selected, no services)
        self.EveryDay.Disable()
        self.Monday.Disable()
        self.Tuesday.Disable()
        self.Wednesday.Disable()
        self.Thursday.Disable()
        self.Friday.Disable()
        self.Saturday.Disable()
        self.Sunday.Disable()
        self.StartTimeCheckBox.Disable()
        self.StartTime.Disable()
        self.EndTimeCheckBox.Disable()
        self.EndTime.Disable()
        self.AllDayCheckBox.Disable()

    def EnableOptions(self):
        self.EveryDay.Enable()
        self.Monday.Enable()
        self.Tuesday.Enable()
        self.Wednesday.Enable()
        self.Thursday.Enable()
        self.Friday.Enable()
        self.Saturday.Enable()
        self.Sunday.Enable()
        self.StartTimeCheckBox.Enable()
        self.StartTime.Enable()
        self.EndTimeCheckBox.Enable()
        self.EndTime.Enable()
        self.AllDayCheckBox.Enable()


    def OnQuit(self, event):
        self.Close()

    def SaveRecord(self, record):
        #Read from time inputs:
        #~ print "Save record %s" % record
        self.services[record]['name'] = self.elb.GetStrings()[record]
        self.services[record]['time'] = self.StartTime.GetValue()
        self.services[record]['endTime'] = self.EndTime.GetValue()
        self.database.UpdateService(self.services[record]['id'],
                                    self.services[record]['name'],
                                    self.services[record]['day'],
                                    self.services[record]['time'],
                                    self.services[record]['endTime'])
        self.database.commit()
        self.services = []
        self.services = self.database.GetServices()
        self.SetAllDay(None)
        print "Commit/Set All Day"

    def OnSave(self, event):
        try:
            self.selected
            self.SaveRecord(self.selected)
        except:
            self.selected = None
        self.Close()

    def SelectItem(self, event):
        event.Skip()

        try:
            self.selected
            self.SaveRecord(self.selected)
        except:
            self.selected = None

        if len(self.elb.GetStrings()) > 0:
            self.EnableOptions()
        else:
            self.DisableOptions()
        listctrl = self.elb.GetListCtrl()
        self.selected = event.m_itemIndex

        try:
            if len(self.elb.GetStrings()) == len(self.services) + 1:
                wx.CallAfter(self.AddAfter) #Until the EditableListCtrl has run it's
                # routine, the new item won't be in elb.GetStrings().
        except AttributeError:
            self.services = []

        if self.selected >= len(self.services):
            #~ print "Not valid"
            pass
        elif not self.services == []:
            #Set selected label:
            self.SelectedText.SetLabel(self.services[self.selected]['name'])
            #Set the selected days:
            day = self.services[self.selected]['day']
            if day  == 0:
                self.EveryDay.SetValue(True)
            elif day == 1:
                self.Monday.SetValue(True)
            elif day == 2:
                self.Tuesday.SetValue(True)
            elif day == 3:
                self.Wednesday.SetValue(True)
            elif day == 4:
                self.Thursday.SetValue(True)
            elif day == 5:
                self.Friday.SetValue(True)
            elif day == 6:
                self.Saturday.SetValue(True)
            elif day == 7:
                self.Sunday.SetValue(True)
            #Set the times:
            self.AllDayCheckBox.SetValue(False)
            if str(self.services[self.selected]['time']) != '':
                self.StartTimeCheckBox.SetValue(True)
                self.StartTime.Enable()
                self.StartTime.SetValue(str(self.services[self.selected]['time']))
                #^ Value must be a string, but database converts it to datetime object

            if str(self.services[self.selected]['endTime']) != '':
                self.EndTimeCheckBox.SetValue(True)
                self.EndTime.Enable()
                self.EndTime.SetValue(str(self.services[self.selected]['endTime']))


            if str(self.services[self.selected]['time']) == '00:00:00' and \
              str(self.services[self.selected]['endTime']) == '23:59:59':
                self.AllDayCheckBox.SetValue(True)
                self.StartTime.Disable()
                self.StartTimeCheckBox.SetValue(False)
                self.EndTime.Disable()
                self.EndTimeCheckBox.SetValue(False)
            elif str(self.services[self.selected]['time']) == '00:00:00':
                #Time is disabled
                self.StartTime.Disable()
                self.StartTime.SetValue('00:00:00')
                self.StartTimeCheckBox.SetValue(False)
            elif str(self.services[self.selected]['endTime']) == '23:59:59':
                #End time is disabled
                self.EndTime.Disable()
                self.EndTime.SetValue('23:59:59')
                self.EndTimeCheckBox.SetValue(False)

            else: #Set stored values:
                if str(self.services[self.selected]['time']) != '00:00:00':
                    self.StartTime.Enable()
                    self.StartTime.SetValue(str(self.services[self.selected]['time']))
                    self.StartTimeCheckBox.SetValue(True)
                else:
                    self.StartTime.Disable()
                    self.StartTime.SetValue('11:00:00')
                    self.StartTimeCheckBox.SetValue(False)

                if str(self.services[self.selected]['endTime']) != '23:59:59':
                    self.EndTime.Enable()
                    self.EndTime.SetValue(str(self.services[self.selected]['endTime']))
                    self.EndTimeCheckBox.SetValue(True)
                else:
                    self.EndTime.Disable()
                    self.EndTime.SetValue('12:00:00')
                    self.EndTimeCheckBox.SetValue(False)


    def SetAllDay(self, event):
        if event:
            checkbox = event.GetEventObject()
        else:
            checkbox = self.AllDayCheckBox
        if checkbox.GetValue():
            self.StartTime.Disable()
            self.StartTime.SetValue('00:00:00')
            self.services[self.selected]['time'] = '00:00:00'
            self.StartTimeCheckBox.SetValue(False)
            self.EndTime.Disable()
            self.EndTime.SetValue('23:59:59')
            self.services[self.selected]['endTime'] = '23:59:59'
            self.EndTimeCheckBox.SetValue(False)
        else:
            self.StartTime.Enable()
            self.StartTime.SetValue('09:00:00')
            self.StartTimeCheckBox.SetValue(True)
            self.EndTime.Enable()
            self.EndTime.SetValue('09:59:59')
            self.EndTimeCheckBox.SetValue(True)

    def SetStartTime(self, event):
        checkbox = event.GetEventObject()
        if checkbox.GetValue():
            self.StartTime.Enable()
            self.AllDayCheckBox.SetValue(False)
            self.StartTime.SetValue('09:00:00')
        else:
            if not self.EndTimeCheckBox.GetValue():
                self.AllDayCheckBox.SetValue(True)
                self.SetAllDay(None) #Set for all day if no times are chosen
            self.StartTime.Disable()
            self.StartTime.SetValue('00:00:00')

    def SetEndTime(self, event):
        checkbox = event.GetEventObject()
        if checkbox.GetValue():
            self.EndTime.Enable()
            self.AllDayCheckBox.SetValue(False)
            self.EndTime.SetValue('09:59:59')
        else:
            if not self.StartTimeCheckBox.GetValue():
                self.AllDayCheckBox.SetValue(True)
                self.SetAllDay(None) #Set for all day if no times are chosen
            self.EndTime.Disable()
            self.EndTime.SetValue('23:59:59')

    def SetEveryDay(self, event):
        self.services[self.selected]['day'] = 0

    def SetMonday(self, event):
        self.services[self.selected]['day'] = 1

    def SetTuesday(self, event):
        self.services[self.selected]['day'] = 2

    def SetWednesday(self, event):
        self.services[self.selected]['day'] = 3

    def SetThursday(self, event):
        self.services[self.selected]['day'] = 4

    def SetFriday(self, event):
        self.services[self.selected]['day'] = 5

    def SetSaturday(self, event):
        self.services[self.selected]['day'] = 6

    def SetSunday(self, event):
        self.services[self.selected]['day'] = 7

    def AddAfter(self):
        #New item, add defaults:
        #~ print "Added service: %s" % self.elb.GetStrings()[-1]

        self.database.AddService(self.elb.GetStrings()[-1], day=0)
        self.services = self.database.GetServices()
        self.SetEveryDay(None)

        #Set selcted item text
        self.SelectedText.SetLabel(self.services[-1]['name'])
        #Set the selected days:
        day = self.services[-1]['day']
        if day  == 0:
            self.EveryDay.SetValue(True)
        elif day == 1:
            self.Monday.SetValue(True)
        elif day == 2:
            self.Tuesday.SetValue(True)
        elif day == 3:
            self.Wednesday.SetValue(True)
        elif day == 4:
            self.Thursday.SetValue(True)
        elif day == 5:
            self.Friday.SetValue(True)
        elif day == 6:
            self.Saturday.SetValue(True)
        elif day == 7:
            self.Sunday.SetValue(True)


    def AddItem(self, event):
        event.Skip()
        #~ self.SetEveryDay(None)
        #~ self.database.AddService(

    def RemoveItem(self, event):
        event.Skip()
        removed = self.services.pop(self.selected)
        self.database.RemoveService(removed['id'])
        #~ self.deleted.append(removed)
        #~ print "Removed service id = %s" % removed['id']


    def UpButtonDisable(self):
        self.UpButton.Disable()


class EditActivities(wx.Dialog):
    def __init__(self, parent, id, database):
        wx.Dialog.__init__(self, parent, id, 'Edit Activities', size=(650,550))
        self.database = database
        self.init_dialog(parent)
        
        #For enumerating nametag templates
        from printing import Nametag
        self.nametags = Nametag().listTemplates()
        
        #populate database values:
        self.activities = database.GetActivities()
        self.elb.SetStrings([ activity['name'] for activity in self.activities ])
        self.SetItem(self.activities[0])
            
        
    def init_dialog(self, parent):
        #Set icon:
        favicon = wx.Icon('resources/taxidi.png', wx.BITMAP_TYPE_PNG, 100, 100)
        self.SetIcon(favicon)
        
        #Activities will be listed here.  Click to edit
        self.elb = gizmos.EditableListBox(self, wx.ID_ANY, "Activities", size=(250,-1))
        self.elb.GetUpButton().Hide()
        self.elb.GetDownButton().Hide()
        self.elb.GetListCtrl().Bind(wx.EVT_LIST_ITEM_SELECTED, self.SelectItem)

        #Set the icons:
        AddButtonIcon = wx.Image('resources/icons/list-add-16.png')
        self.AddButton = self.elb.GetNewButton()
        self.AddButton.SetBitmapLabel(AddButtonIcon.ConvertToBitmap())
        self.AddButton.Bind(wx.EVT_BUTTON, self.AddItem)
        DelButtonIcon = wx.Image('resources/icons/list-remove-16.png')
        self.DelButton = self.elb.GetDelButton()
        self.DelButton.SetBitmapLabel(DelButtonIcon.ConvertToBitmap())
        self.DelButton.Bind(wx.EVT_BUTTON, self.RemoveItem)
        EditButtonIcon = wx.Image('resources/icons/list-edit-16.png')
        self.EditButton = self.elb.GetEditButton()
        self.EditButton.SetBitmapLabel(EditButtonIcon.ConvertToBitmap())
        
        activitySizer = wx.BoxSizer(wx.HORIZONTAL)
        activitySizer.Add(self.elb, 1, wx.ALL|wx.EXPAND, 5 )
    
        controlSizer = wx.BoxSizer(wx.VERTICAL)
        controlSizerb = wx.BoxSizer(wx.VERTICAL)
        
        SelectedSt = wx.StaticText(self, wx.ID_ANY, "Select an activty to edit")
        controlSizerb.Add(SelectedSt, 0, wx.ALL, 8)
        
        pagingSizer = wx.BoxSizer(wx.HORIZONTAL)
    
        #== customPrefixCheckbox ==
        self.customPrefixCheckbox = wx.CheckBox(self, wx.ID_ANY, 
            "Custom paging prefix:")
        pagingSizer.Add(self.customPrefixCheckbox, 0, 
            wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.LEFT, 5)
    
        #== customPrefixText ==
        self.customPrefixText = wx.TextCtrl(self, wx.ID_ANY, "", 
            size=(30,-1), style=wx.TE_CENTRE)
        self.customPrefixText.SetMaxLength( 1 ); 
        pagingSizer.Add(self.customPrefixText, 0, 
            wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.LEFT, 5)
    
        controlSizerb.Add(pagingSizer, 0, wx.EXPAND, 5)
    
        securitySizer = wx.BoxSizer(wx.HORIZONTAL)
        securitySt = wx.StaticText(self, wx.ID_ANY, "Security mode:")
        securitySizer.Add(securitySt, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        
        #== securityChoice
        self.securityChoices = ["None", "Simple (Z99)", u"Secure (Z99 ↔ 5C55)"]
        self.securityChoice = wx.Choice(self, wx.ID_ANY, choices=self.securityChoices)
        #~ self.securityChoice.SetSelection( 2 );
        securitySizer.Add(self.securityChoice, 1, wx.ALL, 5)
        
        controlSizerb.Add(securitySizer, 0, wx.EXPAND, 5)
    
        nametagSizer = wx.FlexGridSizer(2, 2, 0, 0)
        nametagSizer.AddGrowableCol(1)
        nametagSizer.SetFlexibleDirection(wx.BOTH)
        nametagSizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)
        
        self.nametagCheckbox = wx.CheckBox(self, wx.ID_ANY, "Print nametag:")
        nametagSizer.Add(self.nametagCheckbox, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        
        self.nametagTemplateChoice = wx.Choice(self, wx.ID_ANY)
        nametagSizer.Add(self.nametagTemplateChoice, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 3)
        
        self.receiptCheckbox = wx.CheckBox(self, wx.ID_ANY, "Security receipt:")
        nametagSizer.Add(self.receiptCheckbox, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
    
        self.receiptTemplateChoice = wx.Choice(self, wx.ID_ANY)
        nametagSizer.Add(self.receiptTemplateChoice, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 3)
    
        controlSizerb.Add(nametagSizer, 0, wx.EXPAND, 5)
        
        adminSizer = wx.BoxSizer(wx.HORIZONTAL)
    
        adminSt = wx.StaticText(self, wx.ID_ANY, "Administrator:")
        adminSizer.Add(adminSt, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
    
        self.adminTextbox = wx.TextCtrl(self, wx.ID_ANY, "Search...")
        self.adminTextbox.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNSHADOW))
    
        adminSizer.Add(self.adminTextbox, 1, wx.ALL, 3)
    
        controlSizerb.Add(adminSizer, 0, wx.EXPAND, 5)
        
        self.autoCheckoutCheckbox = wx.CheckBox(self, wx.ID_ANY, 
            "Automatic check-out at end of service")
        controlSizerb.Add(self.autoCheckoutCheckbox, 0, wx.RIGHT|wx.LEFT, 5)
    
        self.notifyCheckoutCheckbox = wx.CheckBox(self, wx.ID_ANY, 
            "Notify on auto checkout")
        controlSizerb.Add(self.notifyCheckoutCheckbox, 0, wx.RIGHT|wx.LEFT, 5)
    
        newsletterSizer = wx.BoxSizer(wx.HORIZONTAL)
    
        self.newsletterCheckbox = wx.CheckBox(self, wx.ID_ANY, "Newsletter:")
        newsletterSizer.Add(self.newsletterCheckbox, 0, 
            wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.LEFT, 5)
    
        self.newsletterURLTextbox = wx.TextCtrl(self, wx.ID_ANY)
        self.newsletterURLTextbox.SetToolTip(wx.ToolTip(
            "Enter link to script for adding an email to a mailing " + \
            "list by GET request. {email} will be replaced by the " + \
            "address.\n\nhttp://example.com/newsletter/subscribe.php"+ \
            "?address={email}"))
            
        newsletterSizer.Add(self.newsletterURLTextbox, 1, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)

        controlSizerb.Add(newsletterSizer, 0, wx.EXPAND, 5)
    
        registrationSizera = wx.StaticBoxSizer(wx.StaticBox(self, 
            wx.ID_ANY, "Registration notification"), wx.VERTICAL)
    
        registrationSizerb = wx.BoxSizer(wx.HORIZONTAL)
    
        self.registerSMSCheckbox = wx.CheckBox(self, wx.ID_ANY, "SMS parents")
        registrationSizerb.Add(self.registerSMSCheckbox, 0, 
            wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
    
        self.registerSMSTextbox = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_READONLY)
        registrationSizerb.Add(self.registerSMSTextbox, 1, 
            wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
    
        self.registerSMSButton = wx.Button(self, wx.ID_ANY, "...", size=(26,-1))
        registrationSizerb.Add(self.registerSMSButton, 0, 
            wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
    
        registrationSizera.Add(registrationSizerb, 1, wx.EXPAND, 5)
    
        registrationSizerc = wx.BoxSizer(wx.HORIZONTAL)
    
        self.registerEmailCheckbox = wx.CheckBox(self, wx.ID_ANY,
            "Email parent")
        registrationSizerc.Add(self.registerEmailCheckbox, 0, 
            wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
    
        self.registerEmailTextbox = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_READONLY)
        self.registerEmailTextbox.Enable(False)
        self.registerEmailTextbox.SetToolTip(
            wx.ToolTip("Email templates are " + \
            "located in resources/email/\nEdit the files there to " + \
            "change the message sent to parents after registration."))
    
        registrationSizerc.Add(self.registerEmailTextbox, 1, 
            wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
    
        self.registerEmailButton = wx.Button(self, wx.ID_ANY, "...",
            size=(26,-1))
        self.registerEmailButton.Enable(False);
        self.registerEmailButton.SetToolTip(wx.ToolTip(
            "Edit email templates by opening files in resources/email.  "+ \
            "See wiki for more information."))
            
        registrationSizerc.Add(self.registerEmailButton, 0, 
            wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
    
        registrationSizera.Add(registrationSizerc, 1, wx.EXPAND, 5)
        
        controlSizerb.Add(registrationSizera, 0, wx.EXPAND|wx.BOTTOM|wx.RIGHT|wx.LEFT, 5)
    
        checkinSizera = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, 
            "Check-in notification"), wx.VERTICAL)
    
        checkinSizerb = wx.BoxSizer(wx.HORIZONTAL)
    
        self.checkinSMSCheckbox = wx.CheckBox(self, wx.ID_ANY, "SMS parents")
        checkinSizerb.Add(self.checkinSMSCheckbox, 0, 
            wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
    
        self.checkinSMSTextbox = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_READONLY)
        checkinSizerb.Add(self.checkinSMSTextbox, 1, 
            wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
    
        self.checkinSMSButton = wx.Button(self, wx.ID_ANY, "...", size=(26,-1))
        checkinSizerb.Add(self.checkinSMSButton, 0, 
            wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
    
        checkinSizera.Add(checkinSizerb, 1, wx.EXPAND, 5)
    
        checkinSizerc = wx.BoxSizer(wx.HORIZONTAL)
    
        self.checkinEmailCheckbox = wx.CheckBox(self, wx.ID_ANY, "Email parent")
        checkinSizerc.Add(self.checkinEmailCheckbox, 0, 
            wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
    
        self.checkinEmailTextbox = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_READONLY)
        self.checkinEmailTextbox.Enable(False)
        self.checkinEmailTextbox.SetToolTip(wx.ToolTip(
            "Email templates are located " + \
            "in resources/email/\nEdit the files there to change the " + \
            "message sent to parents after checking in."))
    
        checkinSizerc.Add(self.checkinEmailTextbox, 1, 
            wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
    
        self.checkinEmailButton = wx.Button(self, wx.ID_ANY, "...", size=(26,-1))
        self.checkinEmailButton.Enable(False)
    
        checkinSizerc.Add(self.checkinEmailButton, 0, 
            wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
    
        checkinSizera.Add(checkinSizerc, 1, wx.EXPAND, 5)
    
        controlSizerb.Add(checkinSizera, 0, 
            wx.EXPAND|wx.BOTTOM|wx.RIGHT|wx.LEFT, 5)
    
        #~ controlSizerb.Add(0, 0, 1, wx.EXPAND, 5)
        controlSizerb.AddStretchSpacer()
        
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
    
        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")
        buttonSizer.Add(self.cancelButton, 1, wx.ALL, 5)
    
        self.OKButton = wx.Button(self, wx.ID_OK, "OK")
        buttonSizer.Add(self.OKButton, 1, wx.ALL, 5)
    
        controlSizerb.Add(buttonSizer, 0, 
            wx.ALIGN_RIGHT|wx.BOTTOM|wx.RIGHT|wx.EXPAND, 5)
    
        controlSizer.Add(controlSizerb, 1, wx.EXPAND, 5)
    
        activitySizer.Add(controlSizer, 1, wx.EXPAND|wx.RIGHT, 5)
    
        self.SetSizer(activitySizer)
        self.Layout()
        
        #Bind events
        self.registerSMSButton.Bind(wx.EVT_BUTTON, self.registerSMSEdit)
        self.checkinSMSButton.Bind(wx.EVT_BUTTON, self.checkinSMSEdit)
        self.customPrefixCheckbox.Bind(wx.EVT_CHECKBOX, self.customPrefixToggle)
        self.nametagCheckbox.Bind(wx.EVT_CHECKBOX, self.nametagCheckboxToggle)
        self.receiptCheckbox.Bind(wx.EVT_CHECKBOX, self.receiptCheckboxToggle)
        self.autoCheckoutCheckbox.Bind(wx.EVT_CHECKBOX, self.autoCheckoutCheckboxToggle)
        self.registerSMSCheckbox.Bind(wx.EVT_CHECKBOX, self.registerSMSCheckboxToggle)
        self.checkinSMSCheckbox.Bind(wx.EVT_CHECKBOX, self.checkinSMSCheckboxToggle)

        
    def nametagCheckboxToggle(self, event):
        if self.nametagCheckbox.GetValue():
            self.nametagTemplateChoice.Enable()
        else:
            self.nametagTemplateChoice.Disable()
            
    def receiptCheckboxToggle(self, event):
        if self.receiptCheckbox.GetValue():
            self.receiptTemplateChoice.Enable()
        else:
            self.receiptTemplateChoice.Disable()
            
    def autoCheckoutCheckboxToggle(self, event):
        if self.autoCheckoutCheckbox.GetValue():
            self.notifyCheckoutCheckbox.Enable()
        else:
            self.notifyCheckoutCheckbox.Disable()
        
    def customPrefixToggle(self, event):
        if self.customPrefixCheckbox.GetValue():
            self.customPrefixText.Enable()
        else:
            self.customPrefixText.Disable()
            
    def registerSMSCheckboxToggle(self, event):
        if self.registerSMSCheckbox.GetValue():
            self.registerSMSTextbox.Enable()
            self.registerSMSButton.Enable()
        else:
            self.registerSMSTextbox.Disable()
            self.registerSMSButton.Disable()
            
    def checkinSMSCheckboxToggle(self, event):
        if self.checkinSMSCheckbox.GetValue():
            self.checkinSMSTextbox.Enable()
            self.checkinSMSButton.Enable()
        else:
            self.checkinSMSTextbox.Disable()
            self.checkinSMSButton.Disable()
        
    def SelectItem(self, event):
        event.Skip()

        #~ try:
            #~ self.SaveRecord(self.selected)
        #~ except:
            #~ self.selected = None

        #~ if len(self.elb.GetStrings()) > 0:
            #~ self.EnableOptions()
        #~ else:
            #~ self.DisableOptions()
            
        listctrl = self.elb.GetListCtrl()
        self.selected = event.m_itemIndex
        
        try:
            if len(self.elb.GetStrings()) == len(self.activities) + 1:
                wx.CallAfter(self.AddAfter) #Until the EditableListCtrl has run it's
                # routine, the new item won't be in elb.GetStrings().
        except AttributeError:
            self.activities = [] #All activites removed

        if self.selected >= len(self.activities):
            #~ print "Not valid"
            pass
        elif not self.activities == []:
            #Set selected label:
            pass
        
        try:
            activity = self.activities[self.selected]
            self.SetItem(activity) #Populate fields
        except IndexError:
            #Newly added and not in database/dictionary yet:
            pass
        
    def AddAfter(self):
        print "Add " + self.elb.GetStrings()[-1]
        
    def Reset(self):
        """Resets options to defaults for a new addition"""
        self.customPrefixCheckbox.SetValue(False)
        self.customPrefixText.SetValue("")
        self.customPrefixText.Disable()
        self.securityChoice.Select(0)
        self.nametagCheckbox.SetValue(False)
        self.nametagTemplateChoice.Select(0)
        self.nametagTemplateChoice.Disable()
        self.receiptCheckbox.SetValue(False)
        self.receiptTemplateChoice.Select(0)
        self.receiptTemplateChoice.Disable()
        self.autoCheckoutCheckbox.SetValue(False)
        self.notifyCheckoutCheckbox.SetValue(False)
        self.newsletterCheckbox.SetValue(False)
        self.newsletterURLTextbox.SetValue("http://example.com/list/subscribe.php?addr={email}")
        self.registerSMSCheckbox.SetValue(False)
        self.registerSMSTextbox.Clear()
        self.registerEmailCheckbox.SetValue(False)
        self.checkinSMSCheckbox.SetValue(False)
        self.checkinSMSTextbox.Clear()
        self.checkinEmailCheckbox.SetValue(False)
        
    def SetItem(self, activity):
        """Populate options with data from database"""
        if activity['prefix'] == activity['name'].upper()[0]:
            self.customPrefixCheckbox.SetValue(False)
            self.customPrefixText.SetValue(activity['name'].upper()[0])
            self.customPrefixText.Disable()
        else:
            self.customPrefixCheckbox.SetValue(True)
            self.customPrefixText.SetValue(activity['prefix'])
            self.customPrefixText.Enable()
            
        if activity['securityMode'] == 'none':
            self.securityChoice.Select(0)
        elif activity['securityMode'] == 'simple':
            self.securityChoice.Select(1)
        elif activity['securityMode'] == 'secure':
            self.securityChoice.Select(2)
        else:
            self.securityChoice.Select(0)
            
        self.nametagCheckbox.SetValue(activity['nametagEnable'])
        self.nametagTemplateChoice.SetItems(self.nametags)
        self.nametagTemplateChoice.SetStringSelection(activity['nametag'])
        
        self.receiptCheckbox.SetValue(activity['parentTagEnable'])
        self.receiptTemplateChoice.SetItems(self.nametags)
        self.receiptTemplateChoice.SetStringSelection(activity['parentTag'])
        
        #FIXME: Implement volunteers and admin references
        self.adminTextbox.Disable()
        
        self.autoCheckoutCheckbox.SetValue(activity['autoExpire'])
        if activity['autoExpire']:
            self.notifyCheckoutCheckbox.Enable()
        else:
            self.notifyCheckoutCheckbox.Disable()
        self.notifyCheckoutCheckbox.SetValue(activity['notifyExpire'])
        self.newsletterCheckbox.SetValue(activity['newsletter'])
        if activity['newsletter']:
            self.newsletterURLTextbox.Enable()
        else:
            self.newsletterURLTextbox.Disable()
        self.newsletterURLTextbox.SetValue(activity['newsletterLink'])
        
        self.registerSMSCheckbox.SetValue(activity['registerSMSEnable'])
        if activity['registerSMSEnable']:
            self.registerSMSTextbox.Enable()
            self.registerSMSButton.Enable()
        else:
            self.registerSMSTextbox.Disable()
            self.registerSMSButton.Disable()
        self.registerSMSTextbox.SetValue(activity['registerSMS'].replace('\n','\\n'))
        self.registerEmailCheckbox.SetValue(activity['registerEmailEnable'])
        self.registerEmailTextbox.SetValue(activity['registerEmail'])
        
        self.checkinSMSCheckbox.SetValue(activity['checkinSMSEnable'])
        if activity['checkinSMSEnable']:
            self.checkinSMSTextbox.Enable()
            self.checkinSMSButton.Enable()
        else:
            self.checkinSMSTextbox.Disable()
            self.checkinSMSButton.Disable()
        self.checkinSMSTextbox.SetValue(activity['checkinSMS'].replace('\n','\\n'))
        self.checkinEmailCheckbox.SetValue(activity['checkinEmailEnable'])
        self.checkinEmailTextbox.SetValue(activity['checkinEmail'])
        
        
    def AddItem(self, event):
        self.Reset()
        event.Skip()
        
    def RemoveItem(self, event):
        pass
        
    def registerSMSEdit(self, evt):        
        dlg = EditSMS(self, wx.ID_ANY, 
            self.registerSMSTextbox.GetValue().replace('\\n', '\n'))
        if dlg.ShowModal() == wx.ID_OK:
            self.registerSMSTextbox.SetValue(dlg.GetText().replace('\n', '\\n'))
        dlg.Destroy()
        
    def checkinSMSEdit(self, evt):
        dlg = EditSMS(self, wx.ID_ANY,
            self.checkinSMSTextbox.GetValue().replace('\\n', '\n'))
        if dlg.ShowModal() == wx.ID_OK:
            self.checkinSMSTextbox.SetValue(dlg.GetText().replace('\n', '\\n'))
        dlg.Destroy()
        
        
        
class EditSMS(wx.Dialog):
    def __init__(self, parent, id, text=''):
        pre = wx.PreDialog()
        pre.Create(parent, id, 'Edit SMS Message', size=(365, 190))      
        self.PostCreate(pre)
        self.init_dialog(parent, text)
        
        
    def init_dialog(self, parent, text):
        mainSizer = wx.BoxSizer(wx.VERTICAL)
    
        self.TextBox = wx.TextCtrl(self, wx.ID_ANY, 
            style=wx.TE_LEFT|wx.TE_MULTILINE|wx.TE_WORDWRAP|wx.TE_NO_VSCROLL)
        mainSizer.Add(self.TextBox, 1, wx.ALL|wx.EXPAND, 5)
    
        fieldSizer = wx.BoxSizer(wx.HORIZONTAL)
    
        self.FieldButton = wx.Button(self, wx.ID_ANY, "Insert Field")
        fieldSizer.Add(self.FieldButton, 1, 
            wx.TOP|wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
    
        self.CountSt = wx.StaticText(self, wx.ID_ANY, "Character Count: 0/140")
        fieldSizer.Add(self.CountSt, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
    
        mainSizer.Add(fieldSizer, 0, wx.EXPAND, 5)
    
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
    
        self.CancelButton = wx.Button(self, wx.ID_CANCEL)
        buttonSizer.Add(self.CancelButton, 1, wx.ALL, 5)
    
        self.OKButton = wx.Button(self, wx.ID_OK)
        buttonSizer.Add(self.OKButton, 1, wx.ALL, 5)
    
        mainSizer.Add(buttonSizer, 0, wx.EXPAND, 5)
        self.SetSizer(mainSizer)
        self.Layout()
        
        #Bind events:
        self.Bind(wx.EVT_TEXT, self._updateCharCount)
        self.FieldButton.Bind(wx.EVT_BUTTON, self.onFieldMenu)
        
        self.TextBox.SetValue(text)
        self.TextBox.SetFocus()
        
    def _updateCharCount(self, evt):
        text = self.TextBox.GetValue()
        self.CountSt.SetLabel("Character Count: {0}/140".format(len(text)))
        if len(text) > 140:
            self.CountSt.SetForegroundColour(wx.RED)
        else:
            self.CountSt.SetForegroundColour(
                wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
                
    def onFieldMenu(self, evt):
        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewId()
            self.popupID2 = wx.NewId()
            self.popupID3 = wx.NewId()
            self.popupID4 = wx.NewId()
            self.popupID5 = wx.NewId()
            
        self.Bind(wx.EVT_MENU, self.insertName, id=self.popupID1)
        self.Bind(wx.EVT_MENU, self.insertLastname, id=self.popupID2)
        self.Bind(wx.EVT_MENU, self.insertCode, id=self.popupID3)
        self.Bind(wx.EVT_MENU, self.insertActivity, id=self.popupID4)
        self.Bind(wx.EVT_MENU, self.insertRoom, id=self.popupID5)
        
        menu = wx.Menu()
        menu.Append(self.popupID1, "Name")
        menu.Append(self.popupID2, "Lastname")
        menu.Append(self.popupID3, "Paging Code")
        menu.Append(self.popupID4, "Activity")
        menu.Append(self.popupID5, "Room")
        
        self.PopupMenu(menu)
        menu.Destroy()
        
    def insertName(self, evt):
        self.TextBox.AppendText("{name}")
        self.TextBox.SetFocus()
        
    def insertLastname(self, evt):
        self.TextBox.AppendText("{lastname}")
        self.TextBox.SetFocus()
    
    def insertCode(self, evt):
        self.TextBox.AppendText("{code}")
        self.TextBox.SetFocus()
        
    def insertActivity(self, evt):
        self.TextBox.AppendText("{activity}")
        self.TextBox.SetFocus()
        
    def insertRoom(self, evt):
        self.TextBox.AppendText("{room}")
        self.TextBox.SetFocus()
        
    def GetText(self):
        return self.TextBox.GetValue()
        
        
class BusDialog(wx.Dialog):
    def __init__(self, parent, id):
        pre = wx.PreDialog()
        pre.Create(parent, id, 'Bus Check-in', size=(468, 190))      
        self.PostCreate(pre)
        self.init_dialog(parent)
        
        #Better to do this yourself, to allow for dialogue reuse
        #~ if parent:
            #~ parentPosition = parent.GetPosition()
            #~ self.SetPosition((0, parent.GetPosition()[1] + 100))
            #~ self.CentreOnParent(wx.HORIZONTAL)
        
    def init_dialog(self, parent):
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        nameSizer = wx.BoxSizer(wx.HORIZONTAL)
	
        nameSt = wx.StaticText(self, wx.ID_ANY, "Driver Name")
        nameSizer.Add(nameSt, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
	
        self.NameText = wx.TextCtrl(self, wx.ID_ANY, size=(-1,40))
        self.NameText.SetFont(wx.Font(18, 70, 90, 90, False))
	
        nameSizer.Add(self.NameText, 1, wx.ALIGN_CENTER_VERTICAL|wx.TOP|wx.BOTTOM|wx.LEFT, 5)
	
        KeyboardButton = wx.Button(self, wx.ID_ANY, u"⌨")
        KeyboardButton.SetFont(wx.Font( 18, 70, 90, 90, False))
	
        nameSizer.Add(KeyboardButton, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP|wx.BOTTOM, 5)
        mainSizer.Add(nameSizer, 0, wx.EXPAND|wx.ALL, 5)
        
        numberSizer = wx.BoxSizer(wx.HORIZONTAL)
	
        dlSt = wx.StaticText(self, wx.ID_ANY, "DL #")
        numberSizer.Add(dlSt, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
	
        self.DLText = wx.TextCtrl(self, wx.ID_ANY)
        numberSizer.Add(self.DLText, 1, wx.ALL|wx.EXPAND, 5)
	
        labelsSt = wx.StaticText(self, wx.ID_ANY, "Labels")
        numberSizer.Add(labelsSt, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        
        MinusButton = wx.BitmapButton(self, wx.ID_ANY, wx.Bitmap("resources/icons/list-remove-16.png"), size=(50,-1), style=wx.BU_AUTODRAW)
        numberSizer.Add(MinusButton, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.TOP|wx.BOTTOM|wx.LEFT, 5)
        
        self.LabelsText = wx.TextCtrl(self, wx.ID_ANY, size=(-1,40), style=wx.TE_CENTRE)
        #~ self.LabelsText = wx.lib.masked.NumCtrl(self, wx.ID_ANY, size=(-1,40), style=wx.TE_CENTRE, autoSize = False)
        self.LabelsText.SetFont(wx.Font( 18, 70, 90, 90, False))
        numberSizer.Add(self.LabelsText, 0, wx.TOP|wx.BOTTOM, 5)
        
        PlusButton = wx.BitmapButton(self, wx.ID_ANY, wx.Bitmap("resources/icons/list-add-16.png"), size=(50,-1), style=wx.BU_AUTODRAW)
        numberSizer.Add(PlusButton, 0, wx.EXPAND|wx.TOP|wx.BOTTOM|wx.RIGHT, 5)
        
        mainSizer.Add(numberSizer, 0, wx.EXPAND, 5)
        
        buttonSizer =   wx.BoxSizer(wx.HORIZONTAL)
        
        self.CancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel", size=(-1,50))
        buttonSizer.Add(self.CancelButton, 1, wx.ALL, 5)
        
        OKButton = wx.Button(self, wx.ID_OK, "OK", size=(-1,50))
        buttonSizer.Add(OKButton, 1, wx.ALL, 5)
        
        mainSizer.Add(buttonSizer, 1, wx.EXPAND, 5)
        
        self.SetSizer(mainSizer)
        self.Layout()
        self.NameText.SetFocus()
        
        #Bind events
        KeyboardButton.Bind(wx.EVT_NAVIGATION_KEY, self._tab_pressed1)
        KeyboardButton.Bind(wx.EVT_BUTTON, self.ShowKeyboard)
        MinusButton.Bind(wx.EVT_NAVIGATION_KEY, self._tab_pressed2)
        MinusButton.Bind(wx.EVT_BUTTON, self.RemoveLabel)
        PlusButton.Bind(wx.EVT_NAVIGATION_KEY, self._tab_pressed3)
        PlusButton.Bind(wx.EVT_BUTTON, self.AddLabel)
        
        #Default value
        self.LabelsText.SetValue("1")

    def AddLabel(self, evt):
        value = self.LabelsText.GetValue()
        if not value.isdigit():
            value = "1"
            
        self.LabelsText.SetValue(str(int(value) + 1))
        
    def RemoveLabel(self, evt):
        value = self.LabelsText.GetValue()
        if not value.isdigit():
            value = "1"
            
        self.LabelsText.SetValue(str(int(value) - 1))
        

    def _tab_pressed1(self, evt):
        if evt.IsFromTab():
            if evt.GetDirection():
                self.DLText.SetFocus()
            else:
                self.NameText.SetFocus()
            
    def _tab_pressed2(self, evt):
        if evt.IsFromTab():
            if evt.GetDirection():
                self.LabelsText.SetFocus()
            else:
                self.DLText.SetFocus()
                
    def _tab_pressed3(self, evt):
        if evt.IsFromTab():
            if evt.GetDirection():
                self.CancelButton.SetFocus()
            else:
                self.LabelsText.SetFocus()
                
    def ShowKeyboard(self, event):
        import subprocess
        try:
            subprocess.Popen(('/usr/bin/onboard', '-x', '0', 
                          '-y', '470', '-s', '1024x300'))
        except OSError:
            print "Onboard is not installed.  Unable to open keyboard"
            #~ notify.warning('Onboard not installed', 
                #~ 'Unable to open on-screen keyboard')
        self.NameText.SetFocus()
        
    def GetNameValue(self):
        return self.NameText.GetValue()
        
    def GetDLValue(self):
        return self.DLText.GetValue()
        
    def GetLabelsValue(self):
        return self.LabelsText.GetValue()
        

class HistoryDialog(wx.Dialog):
    def __init__(self, parent, id, history=None, data=None):

        if data != None:
            title = 'Check-in History for {0} {1}'.format(data['name'], data['lastname'])
        else:
            title = 'Check-in History'
        wx.Dialog.__init__(self, parent, id, title, (800,800))
        box1 = wx.BoxSizer(wx.VERTICAL)
        
        toolbar = wx.ToolBar(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TB_HORIZONTAL)
        toolbar.AddLabelTool(10, '', wx.Bitmap("resources/icons/document-save-as-22.png"))
        toolbar.AddLabelTool(20, '', wx.Bitmap("resources/icons/document-print-22.png"))
        self.Bind(wx.EVT_TOOL, self.Save, id=10)
        self.Bind(wx.EVT_TOOL, self.Print, id=20)
        
        
        toolbar.AddSeparator()
        
        self.FilterCheck = wx.CheckBox(toolbar, wx.ID_ANY, "Filter Date:")
        toolbar.AddControl(self.FilterCheck)
        self.FilterDate = wx.DatePickerCtrl(toolbar, size=(120,-1),
                                style = wx.DP_DROPDOWN
                                      | wx.DP_SHOWCENTURY)
        self.Bind(wx.EVT_CHECKBOX, self.OnDateFilter, self.FilterCheck)
        self.Bind(wx.EVT_DATE_CHANGED, self.OnDateChanged, self.FilterDate)
        toolbar.AddControl(self.FilterDate)
                                      
        toolbar.AddSeparator()
        
        toolbar.AddLabelTool(30, '', wx.Bitmap("resources/icons/window-close-22.png"))
        self.Bind(wx.EVT_TOOL, self.quit, id=30)
        toolbar.Realize()
        box1.Add(toolbar, 0, wx.EXPAND, 5)
        
        self.Report = wx.ListCtrl( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LC_REPORT );
        box1.Add(self.Report, 1, wx.EXPAND, 5)
        self.SetSizer(box1)
        self.Layout()
        self.SetSize((800, 600))
        self.Centre(wx.BOTH)
        
        self.Report.InsertColumn(0, 'Date', width=125)
        self.Report.InsertColumn(1, 'Service', width=200)
        self.Report.InsertColumn(2, 'Check-in', width=100)
        self.Report.InsertColumn(3, 'Check-out', width=100)
        self.Report.InsertColumn(4, 'Location', width=125)
        self.Report.InsertColumn(5, 'Room', width=200)
        
        self.history = history
        if history != None:
            self.SetData(history)
            
    def SetData(self, history, date=None):
        index = 0
        for row in history:
            if date != None: #With date filter
                if row['date'] == date: 
                    self.Report.InsertStringItem(index, datetime.datetime.strftime(row['date'], "%a %d %b %Y"))
                    self.Report.SetStringItem(index, 1, row['service'])
                    self.Report.SetStringItem(index, 2, datetime.datetime.strftime(row['checkin'], "%H:%M:%S"))
                    try:
                        self.Report.SetStringItem(index, 3, 
                            datetime.datetime.strftime(row['checkout'], "%H:%M:%S"))
                    except TypeError:
                        self.Report.SetStringItem(index, 3, "n/a")
                    self.Report.SetStringItem(index, 4, row['location'])
                    self.Report.SetStringItem(index, 5, row['room'])
            else: #without
                self.Report.InsertStringItem(index, datetime.datetime.strftime(row['date'], "%a %d %b %Y"))
                self.Report.SetStringItem(index, 1, row['service'])
                self.Report.SetStringItem(index, 2, datetime.datetime.strftime(row['checkin'], "%H:%M:%S"))
                try:
                    self.Report.SetStringItem(index, 3, 
                        datetime.datetime.strftime(row['checkout'], "%H:%M:%S"))
                except TypeError:
                    self.Report.SetStringItem(index, 3, "n/a")
                self.Report.SetStringItem(index, 4, row['location'])
                self.Report.SetStringItem(index, 5, row['room'])
            if index % 2:
                self.Report.SetItemBackgroundColour(index, "white")
            else:
                self.Report.SetItemBackgroundColour(index, "grey")
            index += 1
            
    def OnDateChanged(self, evt):
        if self.FilterCheck.GetValue():
            #Reload with filtered results:
            date = _wxdate2pydate(evt.GetDate())
            self.Report.DeleteAllItems()
            self.SetData(self.history, date)
        
    def OnDateFilter(self, evt):
        if evt.GetEventObject().GetValue():
            date = _wxdate2pydate(self.FilterDate.GetValue())
            self.Report.DeleteAllItems()
            self.SetData(self.history, date)
            
        
    def Save(self, evt):
        dlg = wx.FileDialog(
            self, message="Save file as ...", defaultDir='~', 
            defaultFile="", 
            wildcard="Comma Separated Values (*.csv)|*.csv|" \
            "All files (*.*)|*.*", style=wx.SAVE )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if path[-4:].lower() != '.csv':
                path = path + '.csv'
            f = open(path, 'w')
            f.write('"date","service","checkin","checkout","room","location"\n')
            for row in history:
                f.write('"{0}","{1}","{2}","{3}","{4}","{5}"\n'.format(
                        str(row['date']), row['service'], str(row['checkin']),
                        str(row['checkout']), row['room'], row['location']))
            f.close()
            wx.MessageBox("File was saved as {0}".format(path), "Saved")
        
    def Print(self, evt):
        pass
        
    def quit(self, evt):
        self.EndModal(0)
        
def _wxdate2pydate(date):
     import datetime
     assert isinstance(date, wx.DateTime)
     if date.IsValid():
         ymd = map(int, date.FormatISODate().split('-'))
         return datetime.date(*ymd)
     else:
         return None

# --- Sample Usage ---
if __name__ == '__main__':
    #print askLogin('john_doe', '123', mayCancel=False)
    #~ print askLogin()
    #~ print askPass()

    #Services management dialog:
    app = wx.PySimpleApp(0)

    #~ from dblib import sqlite
    #~ db = sqlite.Database('~/.taxidi/database/users.db')
#~ 
    #~ dlg = EditServices(None, -1, db)
    #~ services = db.GetServices()
    #~ dlg.SetServices(services)
#~ 
    #~ dlg.ShowModal()
    #~ db.commit()

    #changed = [i for i in dlg.GetServices() if i not in db.GetServices() or i not in dlg.GetServices()]
    
    #~ import datetime
    #~ 
    #~ history = [{'checkin': datetime.datetime(2012, 6, 16, 10, 19, 54, 133162),
  #~ 'checkout': datetime.datetime(2012, 6, 16, 10, 25, 4, 653988),
  #~ 'date': datetime.date(2012, 6, 16),
  #~ 'location': 'Kiosk1',
  #~ 'service': 'First Service',
  #~ 'room': 'Butterflies'},
 #~ {'checkin': datetime.datetime(2012, 6, 16, 10, 19, 54, 135601),
  #~ 'checkout': datetime.datetime(2012, 6, 16, 10, 25, 4, 653988),
  #~ 'date': datetime.date(2012, 6, 16),
  #~ 'location': 'Kiosk1',
  #~ 'service': 'Second Service',
  #~ 'room': 'Butterflies'}]
#~ 
    #~ 
    #~ dlg = HistoryDialog(None, wx.ID_ANY, history)
    #~ dlg.ShowModal()
#~ 
    #~ dlg.Destroy()
    
    #~ dlg = EditActivities(None, -1, db)
    #~ dlg.ShowModal()
    #~ dlg.Destroy()
    #~ db.commit()
    #~ db.close()
    
    #Bus ministry
    dlg = BusDialog(None, -1)
    dlg.ShowModal()
    dlg.Destroy()
    
    #~ dlg = EditSMS(None, -1, "Testing 123")
    #~ if dlg.ShowModal() == wx.ID_OK:
        #~ print "OK! Got text:"
        #~ print "'{0}'".format(dlg.GetText())
    #~ else:
        #~ print "You pressed Cancel"
    #~ dlg.Destroy()
    
    app.MainLoop()
