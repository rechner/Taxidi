
#TODO: rewrite this with logging and make it pretty.
#TODO: Add password checking, keep user/pass prompt open until checking is done.

#FIXME: RCX incorrectly complains "Cannot load resources from file" despite loading them anyways. (?)

import os
import wx
from wx import xrc


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



# --- Sample Usage ---
import sys

if __name__ == '__main__':
    #print askLogin('john_doe', '123', mayCancel=False)
    print askLogin()
    print askPass()
