
#TODO: rewrite this with logging and make it pretty.
#TODO: Add password checking, keep user/pass prompt open until checking is done.

#FIXME: RCX incorrectly complains "Cannot load resources from file" despite loading them anyways. (?)

import os
import wx
from wx import xrc
import wx.gizmos as gizmos
import wx.lib.masked as masked

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
        #~ #TODO: Get data from database

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
        print "Commit"

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
            if self.services[self.selected]['time'] != '':
                self.StartTimeCheckBox.SetValue(True)
                self.StartTime.Enable()
                self.StartTime.SetValue(self.services[self.selected]['time'])

            if self.services[self.selected]['endTime'] != '':
                self.EndTimeCheckBox.SetValue(True)
                self.EndTime.Enable()
                self.EndTime.SetValue(self.services[self.selected]['endTime'])


            if self.services[self.selected]['time'] == '00:00:00' and \
              self.services[self.selected]['endTime'] == '23:59:59':
                self.AllDayCheckBox.SetValue(True)
                self.StartTime.Disable()
                self.StartTimeCheckBox.SetValue(False)
                self.EndTime.Disable()
                self.EndTimeCheckBox.SetValue(False)
            elif self.services[self.selected]['time'] == '00:00:00':
                #Time is disabled
                self.StartTime.Disable()
                self.StartTime.SetValue('00:00:00')
                self.StartTimeCheckBox.SetValue(False)
            elif self.services[self.selected]['endTime'] == '23:59:59':
                #End time is disabled
                self.EndTime.Disable()
                self.EndTime.SetValue('23:59:59')
                self.EndTimeCheckBox.SetValue(False)

            else: #Set stored values:
                if self.services[self.selected]['time'] != '00:00:00':
                    self.StartTime.Enable()
                    self.StartTime.SetValue(self.services[self.selected]['time'])
                    self.StartTimeCheckBox.SetValue(True)
                else:
                    self.StartTime.Disable()
                    self.StartTime.SetValue('11:00:00')
                    self.StartTimeCheckBox.SetValue(False)

                if self.services[self.selected]['endTime'] != '23:59:59':
                    self.EndTime.Enable()
                    self.EndTime.SetValue(self.services[self.selected]['endTime'])
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
        #~ self.database.AddService(

    def RemoveItem(self, event):
        event.Skip()
        removed = self.services.pop(self.selected)
        self.database.RemoveService(removed['id'])
        #~ self.deleted.append(removed)
        #~ print "Removed service id = %s" % removed['id']


    def UpButtonDisable(self):
        self.UpButton.Disable()




# --- Sample Usage ---
if __name__ == '__main__':
    #print askLogin('john_doe', '123', mayCancel=False)
    #~ print askLogin()
    #~ print askPass()

    #Services management dialog:
    app = wx.PySimpleApp(0)

    from dblib import sqlite
    db = sqlite.Database('~/.taxidi/database/users.db')

    dlg = EditServices(None, -1, db)
    services = db.GetServices()
    dlg.SetServices(services)

    dlg.ShowModal()
    db.commit()

    #changed = [i for i in dlg.GetServices() if i not in db.GetServices() or i not in dlg.GetServices()]

    dlg.Destroy()
    app.MainLoop()
