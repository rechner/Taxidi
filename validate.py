#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
This is for formatting and validating phone numbers, etc. in Taxidi.
"""

emailRegex = "^[a-zA-Z0-9._%-+]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$"

import re
import string
from wx import NullColour

def Translator(frm='', to='', delete='', keep=None):
    """
    Wrapper around string.translate().
    Note that translate() does not support unicode objects.

    """
    allchars = string.maketrans('','')
    if len(to) == 1:
        to = to * len(frm)
    trans = string.maketrans(frm, to)
    if keep is not None:
        delete = allchars.translate(allchars, keep.translate(allchars, delete))
    def callable(s):
        return s.translate(trans, delete)
    return callable


def PhoneFormat(phone):
    """
    Validates input from a wx.TextBox against 10-digit NANP (North America)
    and the international direct dialing format.  Allowed formats are:
      4805551212
      (480) 555-1212
      334-555-1212
      +49 (0)152.25.25/1212

    NANP 10-digit numbers are automatically displayed in (###) ###-#### format.

    `phone`: The event's GetEventObject(), or the wx.TextControl to validate.
    The complete, unformatted number is stored as a string in the passed object's
    unformatted property.

    e.x.
    self.TextBox.Bind(wx.EVT_TEXT, self.OnTextChange)
    ...
    def OnTextChange(self, event):
      phone = event.GetEventObject()
      validate.PhoneFormat(phone)
    """
    value = phone.GetValue()
    if value.isdigit() and len(value) == 10 \
      and value[0] not in '01' and value[3] not in '01':  #US: '4805551212'
        phone.ChangeValue('(%s) %s-%s' % (value[0:3], value[3:6], value[6:10]))
        phone.SetBackgroundColour('green')
        phone.unformatted = value  #Number is already unformatted

    elif len(value) == 0: #Do nothing if blank.
        phone.SetBackgroundColour(NullColour)
        phone.unformatted = value

    elif len(value) == 12 and value[3] in '.-/' \
      and value[7] in '.-/':  #US: '334-555-1212'
        trans = Translator(delete='+(-)./ ')
        value = trans(value.encode('ascii'))
        phone.unformatted = value
        phone.SetValue('(%s) %s-%s' % (value[0:3], value[3:6], value[6:10]))
        phone.SetBackgroundColour('green')
        phone.SetInsertionPointEnd() #Sometimes the cursor ends up in the middle

    elif value[0] == '(' and len(value) == 14: #reformat if changed (US)
        value = value[1:4] + value[6:9] + value[10:14]
        phone.unformatted = value
        phone.ChangeValue('(%s) %s-%s' % (value[0:3], value[3:6], value[6:10]))
        phone.SetBackgroundColour('green')
        phone.SetInsertionPointEnd()

    elif value[0] == '+':
        trans = Translator(delete='+(-)./ ')
        unformatted = trans(value.encode('ascii')) #doesn't work with unicode.
        if unformatted.isdigit(): #International
            phone.SetBackgroundColour('lightgreen')

    else: #Probably not a phone number
        phone.SetBackgroundColour('red')
        phone.unformatted = ''
        return 1

def EmailFormat(email):
    value = email.GetValue()
    if len(value) == 0:
        email.SetBackgroundColour(NullColour)
        return 0
    if Email(value):
        email.SetBackgroundColour('green')
    else:
        email.SetBackgroundColour('pink')

def DateFormatPost(date):
    #Clear the input if needed
    value = date.GetValue()
    if value == '':
        date.SetValue('YYYY-MM-DD')
        date.SetForegroundColour('#cdcdcd')
        date.SetBackgroundColour(NullColour)
    if len(value) == 9: #2011-9-14 or 2011-09-5
        if value[4] in '-./\\' and value[5].isdigit() and value[6] in '-./\\':
            #YYYY-M-DD
            date.SetValue('{0}-0{1}-{2}'.format(value[0:4], value[5:6], value[7:9]))
            date.SetBackgroundColour('green')
            date.SetInsertionPointEnd()
        elif value[4] in '-./\\' and value[5:7].isdigit() and value[7] in '-./\\':
            #YYYY-MM-D
            date.SetValue('{0}-{1}-0{2}'.format(value[0:4], value[5:7], value[8:9]))
            date.SetBackgroundColour('green')
            date.SetInsertionPointEnd()


def DateFormat(date):
    value = date.GetValue()
    import wx
    wxApp = wx.GetApp() #Get the current wx.App(), if possible.
    if not wxApp:
        foreground = 'black'
    else: #Set the appropriate system text colour
        foreground = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
    date.SetForegroundColour(foreground)
    #~ if len(value) == 0:
        #~ date.SetBackgroundColour(NullColour)
        #~ date.SetForegroundColour('#cdcdcd')
        #~ date.SetValue('YYYY-MM-DD')
        #~ date.SelectAll()
    valid = False
    if len(value) > 1:
        date.SetBackgroundColour('pink')
    else:
        date.SetBackgroundColour(NullColour)
    if len(value) == 8 and value.isdigit():
        date.SetValue('{0}-{1}-{2}'.format(value[0:4], value[4:6], value[6:8]))
        date.SetBackgroundColour('green')
        date.SetInsertionPointEnd()
        valid = True
    if len(value) == 10:
        if value == 'YYYY-MM-DD':
            date.Clear()
            date.SetForegroundColour(foreground)
            valid = False
        else:
            if (value[0:4]+value[5:7]+value[8:10]).isdigit():
                #Format is correct. Replace separators:
                trans = Translator(delete='-./\\ ')
                unformat = trans(value.encode('ascii')) #doesn't work with unicode.
                date.SetValue('{0}-{1}-{2}'.format(unformat[0:4], unformat[4:6], unformat[6:8]))
                date.SetBackgroundColour('green')
                date.SetInsertionPointEnd()
                valid = True
                if int(value[5:7]) > 12 or int(value[8:10]) > 31: #check day/month ranges
                    date.SetBackgroundColour('red')
                    valid = False
            else:
                date.SetBackgroundColour('pink')
                valid = False
    return valid

def Email(email):
    """
    Validates an email format.  Returns 1 if valid, 0 if invalid.
    """

    if re.match(emailRegex, email) != None:
        return 1
    return 0
