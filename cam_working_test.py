import wx 
from opencv import cv, highgui 
import opencv


class LivePanel(wx.Panel): 
    def __init__(self, parent, id): 
        wx.Panel.__init__(self, parent, id) 
        self.cap = highgui.cvCreateCameraCapture(0) 
        self.Bind(wx.EVT_IDLE, self.onIdle) 
        
    def onIdle(self, event): 
        img = highgui.cvQueryFrame(self.cap) 
        img = opencv.cvGetMat(img)
        cv.cvCvtColor(img, img, cv.CV_BGR2RGB)
        self.displayImage(img) 
        event.RequestMore()
        
    def displayImage(self, img, offset=(0,0)): 
        bitmap = wx.BitmapFromBuffer(img.width, img.height, img.imageData) 
        dc = wx.ClientDC(self) 
        dc.DrawBitmap(bitmap, offset[0], offset[1], False) 
        
    def save(self):
        print "Save"
        img = highgui.cvQueryFrame(self.cap)
        img = opencv.cvGetMat(img)
        #No BGR => RGB conversion needed for PIL output.
        pil = opencv.adaptors.Ipl2PIL(img)  #convert to a PIL
        pil.save('out.jpg')
        
        
t_CONTROLS_PLAY = wx.NewEventType()
CONTROLS_PLAY = wx.PyEventBinder(t_CONTROLS_PLAY, 1)
t_CONTROLS_STOP = wx.NewEventType()
CONTROLS_STOP = wx.PyEventBinder(t_CONTROLS_STOP, 1)

class Controls(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # Controls
        self.button_play = wx.Button(self, label="Take Picture")
        self.button_stop = wx.Button(self, label="Stop")    

        # Sizer
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.button_play)
        sizer.Add(self.button_stop)
        self.SetSizer(sizer)

        # Events
        self.button_play.Bind(wx.EVT_BUTTON, self.Snapshot)
        self.button_stop.Bind(wx.EVT_BUTTON, self.OnStop)

    def Snapshot(self, evt):
        evt2 = wx.PyCommandEvent(t_CONTROLS_PLAY, self.GetId())
        self.GetEventHandler().ProcessEvent(evt2)
        evt.Skip()

    def OnStop(self, evt):
        #close
        evt.Skip()
        
class Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # Controls
        self.live = LivePanel(self, -1)
        self.controls  = Controls(self)

        # Sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.live, 1, wx.RIGHT|wx.EXPAND, 4)
        sizer.Add(self.controls, 0, wx.ALL|wx.EXPAND, 4)
        self.SetSizer(sizer)

        # Events
        self.controls.Bind(CONTROLS_PLAY, self.OnPlay)
        self.controls.Bind(CONTROLS_STOP, self.OnStop)

    def OnPlay(self, evt):
        self.live.save()

    def OnStop(self, evt):
        pass
        #self.input_viewer.stop()

        
# Main Procedure 
app = wx.PySimpleApp() 
pFrame = wx.Frame(None, -1, "Media Player", size = (640, 480))
Panel(pFrame)
pFrame.Show() 
app.MainLoop() 
