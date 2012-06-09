# Main ToasterBoxDemo

import wx
import ToasterBox as TB

# In Case Of TB_COMPLEX Style, Create A Panel That Contains An Image, Some
# Text, An Hyperlink And A Ticker.

import wx.lib.hyperlink as hyperlink
from wx.lib.ticker import Ticker

#----------------------------------------------------------------------
# Get Some Icon/Data
#----------------------------------------------------------------------

def GetMondrianData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00 \x00\x00\x00 \x08\x06\x00\
\x00\x00szz\xf4\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\x00\x00qID\
ATX\x85\xed\xd6;\n\x800\x10E\xd1{\xc5\x8d\xb9r\x97\x16\x0b\xad$\x8a\x82:\x16\
o\xda\x84pB2\x1f\x81Fa\x8c\x9c\x08\x04Z{\xcf\xa72\xbcv\xfa\xc5\x08 \x80r\x80\
\xfc\xa2\x0e\x1c\xe4\xba\xfaX\x1d\xd0\xde]S\x07\x02\xd8>\xe1wa-`\x9fQ\xe9\
\x86\x01\x04\x10\x00\\(Dk\x1b-\x04\xdc\x1d\x07\x14\x98;\x0bS\x7f\x7f\xf9\x13\
\x04\x10@\xf9X\xbe\x00\xc9 \x14K\xc1<={\x00\x00\x00\x00IEND\xaeB`\x82' 

def GetMondrianBitmap():
    return wx.BitmapFromImage(GetMondrianImage())

def GetMondrianImage():
    import cStringIO
    stream = cStringIO.StringIO(GetMondrianData())
    return wx.ImageFromStream(stream)

def GetMondrianIcon():
    icon = wx.EmptyIcon()
    icon.CopyFromBitmap(GetMondrianBitmap())
    return icon

# ------------------------------------------------------------------------------ #
# Class ToasterBoxDemo
#    This Class Implements The Demo For ToasterBox Control. Try To Change The
#    Style Using The RadioBox In The Upper Section Of The Frame, And See How
#    ToasterBox Acts.
# ------------------------------------------------------------------------------ #

class ToasterBoxDemo(wx.Frame):

    def __init__(self, parent, id=wx.ID_ANY, title="ToasterBox Demo",
                 pos = wx.DefaultPosition, size=(400,550)):

        wx.Frame.__init__(self, parent, id, title, pos, size)
        self.SetIcon(GetMondrianIcon())
        
        pn = wx.Panel(self, -1)
        mainSz = wx.BoxSizer(wx.VERTICAL)

        horSz0 = wx.BoxSizer(wx.HORIZONTAL)
        mainSz.Add((0, 3))
        mainSz.Add(horSz0, 1, wx.EXPAND | wx.BOTTOM, 7)

        sampleList = [" ToasterBox With TB_SIMPLE ", " ToasterBox With TB_COMPLEX "]
        rb = wx.RadioBox(pn, -1, "ToasterBox Style", wx.DefaultPosition,
                         wx.DefaultSize, sampleList, 2, wx.RA_SPECIFY_COLS)

        horSz0.Add(rb, 1, 0, 5)        
        rb.SetToolTip(wx.ToolTip("Choose The ToasterBox Style"))

        self.radiochoice = rb
                
        horSz1 = wx.BoxSizer(wx.HORIZONTAL)
        mainSz.Add(horSz1, 1, wx.EXPAND | wx.ALL, 5)
        
        statTxt1 = wx.StaticText(pn, -1, "Popup Position x/y")
        horSz1.Add(statTxt1, 3)
        txtCtrl1 = wx.TextCtrl(pn, -1, "500")
        horSz1.Add(txtCtrl1, 1)
        txtCtrl1b = wx.TextCtrl(pn, -1, "500")
        horSz1.Add(txtCtrl1b, 1)

        self.posx = txtCtrl1
        self.posy = txtCtrl1b

        horSz2 = wx.BoxSizer(wx.HORIZONTAL)
        mainSz.Add(horSz2, 1, wx.EXPAND | wx.ALL, 5)
        
        statTxt2 = wx.StaticText(pn, -1, "Popup Size x/y")
        horSz2.Add(statTxt2, 3)
        txtCtrl2 = wx.TextCtrl(pn, -1, "210")
        horSz2.Add(txtCtrl2, 1)
        txtCtrl3 = wx.TextCtrl(pn, -1, "130")
        horSz2.Add(txtCtrl3, 1)

        self.sizex = txtCtrl2
        self.sizey = txtCtrl3
        
        horSz3 = wx.BoxSizer(wx.HORIZONTAL)
        mainSz.Add(horSz3, 1, wx.EXPAND | wx.ALL, 5)
        
        statTxt3 = wx.StaticText(pn, -1, "Popup Linger")
        horSz3.Add(statTxt3, 3)
        txtCtrl4 = wx.TextCtrl(pn, -1, "4000")
        helpstr = "How Long The Popup Will Stay\nAround After It Is Launched"
        txtCtrl4.SetToolTip(wx.ToolTip(helpstr))
        horSz3.Add(txtCtrl4, 1)

        self.linger = txtCtrl4

        horSz3b = wx.BoxSizer(wx.HORIZONTAL)
        mainSz.Add(horSz3b, 1, wx.EXPAND | wx.ALL, 5)
        statTxt3b = wx.StaticText(pn, -1, "Popup Scroll Speed")
        horSz3b.Add(statTxt3b, 3)
        txtCtrl4b = wx.TextCtrl(pn, -1, "8")
        helpstr = "How Long It Takes The Window To \"Fade\" In And Out"
        txtCtrl4b.SetToolTip(wx.ToolTip(helpstr))
        horSz3b.Add(txtCtrl4b, 2)

        self.scrollspeed = txtCtrl4b

        horSz3c = wx.BoxSizer(wx.HORIZONTAL)
        mainSz.Add(horSz3c, 1, wx.EXPAND | wx.ALL, 5)  
        statTxt3c = wx.StaticText(pn, -1, "Popup Background Picture")
        horSz3c.Add(statTxt3c, 3)
        txtCtrl4c = wx.TextCtrl(pn, -1, "bg.bmp")
        helpstr = "You Can Add A .bmp File As The Background To The Popup Window. " \
                  "The Picture Will Autosize To The Window"
        txtCtrl4c.SetToolTip(wx.ToolTip(helpstr))
        horSz3c.Add(txtCtrl4c, 2)

        self.backimage = txtCtrl4c

        popupText1 = "Hello From wxPython! This Is Another (Probably) Useful Class. " \
                    "Written By Andrea Gavana @ 8 September 2005."
        popupText2 = "I Don't Know What To Write In This Message. If You Like This. " \
                    "Class, Please Let Me Know!."
        
        horSz4 = wx.BoxSizer(wx.HORIZONTAL)
        mainSz.Add(horSz4, 1, wx.EXPAND | wx.ALL, 5)
        statTxt4 = wx.StaticText(pn, -1, "Popup Text")
        horSz4.Add(statTxt4, 1)
        txtCtrl5 = wx.TextCtrl(pn, -1, popupText1)
        txtCtrl5.SetToolTip(wx.ToolTip("What The Text In The Popup Should Say."))
        horSz4.Add(txtCtrl5, 2)

        self.showntext = txtCtrl5
        self.popupText1 = popupText1
        self.popupText2 = popupText2
        self.counter = 0

        horSz5 = wx.BoxSizer(wx.HORIZONTAL)
        mainSz.Add(horSz5, 1, wx.EXPAND | wx.ALL, 5)
        self.colButton1 = wx.Button(pn, -1, "Set BG Color")
        self.colButton1.SetToolTip(wx.ToolTip("Set The ToasterBox Background Colour"))
        self.colButton1.Bind(wx.EVT_BUTTON, self.SetColors)
        horSz5.Add(self.colButton1, 1, 0, 5)
        self.colButton2 = wx.Button(pn, -1, "Set FG Color")
        self.colButton2.SetToolTip(wx.ToolTip("Set The ToasterBox Text Colour"))
        self.colButton2.Bind(wx.EVT_BUTTON, self.SetColors2)
        horSz5.Add(self.colButton2, 1, 0, 5)

        horSz6 = wx.BoxSizer(wx.HORIZONTAL)
        mainSz.Add(horSz6, 1, wx.EXPAND | wx.ALL, 5)
        statTxt6 = wx.StaticText(pn, -1, "Popup Text Font")
        horSz6.Add(statTxt6, 1, 0, 5)
        fontbutton = wx.Button(pn, -1, "Select Font")
        horSz6.Add(fontbutton, 1, 0, 5)

        horSz7 = wx.BoxSizer(wx.HORIZONTAL)
        mainSz.Add(horSz7, 1, wx.EXPAND | wx.ALL, 5)
        self.checkcaption = wx.CheckBox(pn, -1, "Show With Caption")
        horSz7.Add(self.checkcaption, 1, 0, 5)
        self.captiontext = wx.TextCtrl(pn, -1, "ToasterBox Title!")
        horSz7.Add(self.captiontext, 1, 0, 5)
        self.captiontext.Enable(False)
        self.checkcaption.Bind(wx.EVT_CHECKBOX, self.OnCheckCaption)

        horSz8 = wx.BoxSizer(wx.VERTICAL)
        mainSz.Add(horSz8, 1, wx.EXPAND | wx.ALL, 5)
        self.radiotime = wx.RadioButton(pn, -1, "Hide By Time", style=wx.RB_GROUP)
        horSz8.Add(self.radiotime, 1, 0, 5)
        self.radioclick = wx.RadioButton(pn, -1, "Hide By Click")
        horSz8.Add(self.radioclick, 1, 0, 5)
        
        horSz9 = wx.BoxSizer(wx.HORIZONTAL)
        mainSz.Add(horSz9, 1, wx.EXPAND | wx.ALL, 5)
        goButton = wx.Button(pn, -1, "Show ToasterBox!")
        goButton.SetToolTip(wx.ToolTip("Launch ToasterBox. You Can Click More Than Once!"))
        horSz9.Add((1,0), 1)
        horSz9.Add(goButton, 2, 0, 5)
        horSz9.Add((1,0), 1)

        self.colButton1.SetBackgroundColour(wx.WHITE)
        self.colButton2.SetBackgroundColour(wx.BLACK)
        self.colButton2.SetForegroundColour(wx.WHITE)

        goButton.Bind(wx.EVT_BUTTON, self.ButtonDown)
        fontbutton.Bind(wx.EVT_BUTTON, self.OnSelectFont)
        rb.Bind(wx.EVT_RADIOBOX, self.OnRadioBox)
        
        self.curFont = self.GetFont()
        
        pn.SetAutoLayout(True)
        pn.SetSizer(mainSz)
        pn.Fit()


    def SetColors(self, event):
        
        cd = wx.ColourDialog(self)
        cd.ShowModal()
        colBg = cd.GetColourData().GetColour()
        colButton1 = event.GetEventObject()
        colButton1.SetBackgroundColour(colBg)  


    def SetColors2(self, event):
        
        cd = wx.ColourDialog(self)
        cd.ShowModal()
        colFg = cd.GetColourData().GetColour()
        colButton2 = event.GetEventObject()
        colButton2.SetBackgroundColour(colFg)  


    def OnSelectFont(self, event):

        curFont = self.GetFont()
        curClr = wx.BLACK
        data = wx.FontData()
        data.EnableEffects(True)
        data.SetColour(curClr)
        data.SetInitialFont(curFont)
        
        dlg = wx.FontDialog(self, data)
        
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetFontData()
            font = data.GetChosenFont()
            colour = data.GetColour()

            self.curFont = font
            self.curClr = colour

        dlg.Destroy()        
    

    def OnRadioBox(self, event):

        mainsizer = self.GetChildren()[0].GetSizer()
        
        if event.GetInt() == 0:
            self.linger.SetValue("4000")
            self.scrollspeed.SetValue("8")
            
            for ii in xrange(5, 10):
                mainsizer.Show(ii, True)
                        
        else:
            for ii in xrange(5, 10):
                mainsizer.Show(ii, False)

            self.linger.SetValue("10000")
            self.scrollspeed.SetValue("20")

        mainsizer.Layout()
        self.Refresh()
        
        event.Skip()
        

    def OnCheckCaption(self, event):

        if self.checkcaption.GetValue():
            self.captiontext.Enable(True)
            self.sizex.SetValue("220")
            self.sizey.SetValue("160")
        else:
            self.captiontext.Enable(False)
            self.sizex.SetValue("210")
            self.sizey.SetValue("130")

        self.sizex.Refresh()
        self.sizey.Refresh()
        

    def ButtonDown(self, event):

        demochoice = self.radiochoice.GetSelection()

        if self.checkcaption.GetValue():
            txts = self.captiontext.GetValue().strip()
            windowstyle = TB.TB_CAPTION
        else:
            windowstyle = TB.DEFAULT_TB_STYLE
        
        if demochoice == 1:
            tbstyle = TB.TB_COMPLEX
        else:
            tbstyle = TB.TB_SIMPLE

        if self.radioclick.GetValue():
            closingstyle = TB.TB_ONCLICK
        else:
            closingstyle = TB.TB_ONTIME
            
        tb = TB.ToasterBox(self, tbstyle, windowstyle, closingstyle)

        if windowstyle == TB.TB_CAPTION:
            tb.SetTitle(txts)

        sizex = int(self.sizex.GetValue())
        sizey = int(self.sizey.GetValue())
        tb.SetPopupSize((sizex, sizey))

        posx = int(self.posx.GetValue())
        posy = int(self.posy.GetValue())
        tb.SetPopupPosition((posx, posy))
        
        tb.SetPopupPauseTime(int(self.linger.GetValue()))
        tb.SetPopupScrollSpeed(int(self.scrollspeed.GetValue()))

        if demochoice == 0:    # Simple Demo:

            self.RunSimpleDemo(tb)

        else:

            self.RunComplexDemo(tb)            
        
        tb.Play()


    def RunSimpleDemo(self, tb):

        tb.SetPopupBackgroundColor(self.colButton1.GetBackgroundColour())
        tb.SetPopupTextColor(self.colButton2.GetBackgroundColour())
        dummybmp = wx.Bitmap(self.backimage.GetValue(), wx.BITMAP_TYPE_BMP)

        if dummybmp.Ok():
            tb.SetPopupBitmap(self.backimage.GetValue())
        else:
            tb.SetPopupBitmap()

        txtshown = self.showntext.GetValue()
        if self.counter == 0:
            if txtshown in [self.popupText1, self.popupText2]:
                self.counter = self.counter + 1
                txtshown = self.popupText1
        else:
            if txtshown in [self.popupText1, self.popupText2]:
                self.counter = 0
                txtshown = self.popupText2             
             
        tb.SetPopupText(txtshown)
        tb.SetPopupTextFont(self.curFont)
            

    def RunComplexDemo(self, tb):

        # This Is The New Call Style: The Call To GetToasterBoxWindow()
        # Is Mandatory, In Order To Create A Custom Parent On ToasterBox.
        
        tbpanel = tb.GetToasterBoxWindow()
        panel = wx.Panel(tbpanel, -1)

        sizer = wx.BoxSizer(wx.VERTICAL)
        horsizer1 = wx.BoxSizer(wx.HORIZONTAL)

        myimage = wx.Bitmap("andrea.jpeg", wx.BITMAP_TYPE_JPEG)
        stbmp = wx.StaticBitmap(panel, -1, myimage)
        horsizer1.Add(stbmp, 0)

        strs = "This Is Another Example Of ToasterBox, A Complex One. This Kind Of"
        strs = strs + " ToasterBox Can Be Created Using The Style TB_COMPLEX."
        sttext = wx.StaticText(panel, -1, strs)
        sttext.SetFont(wx.Font(7, wx.SWISS, wx.NORMAL, wx.NORMAL, False, "Verdana"))
        horsizer1.Add(sttext, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        hl = hyperlink.HyperLinkCtrl(panel, -1, "My Home Page",
                                     URL="http://xoomer.virgilio.it/infinity77/")

        sizer.Add((0,5))        
        sizer.Add(horsizer1, 0, wx.EXPAND)

        horsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        horsizer2.Add((5, 0))
        horsizer2.Add(hl, 0, wx.EXPAND | wx.TOP, 10)
        sizer.Add(horsizer2, 0, wx.EXPAND)

        tk = Ticker(panel)
        tk.SetText("Hello From wxPython!")
        
        horsizer3 = wx.BoxSizer(wx.HORIZONTAL)
        horsizer3.Add((5, 0))
        horsizer3.Add(tk, 1, wx.EXPAND | wx.TOP, 10)
        horsizer3.Add((5,0))
        sizer.Add(horsizer3, 0, wx.EXPAND)
        
        sizer.Layout()
        panel.SetSizer(sizer)
        
        tb.AddPanel(panel)
        

def main():

    app = wx.PySimpleApp()
    frame = ToasterBoxDemo(None)
    frame.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()

    