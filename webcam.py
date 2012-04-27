#!/usr/bin/env python
#-*- coding:utf-8 -*-

#TODO: Implement file system organization, handle uploading image to server.

import wx
from opencv import cv, highgui
import opencv

class LivePanel(wx.Panel):
    """
    Creates a  wxPanel for capturing from an USB webcam with OpenCV, meaning
    this works with all platforms OpenCV works with (Linux, OS X, Windows).

    Initialize just like a wx.Panel, optionally specifying a camera index, starting
    from 0.  Default of -1 will automatically select the first useable device.
    """
    def __init__(self, parent, id, camera=-1):
        wx.Panel.__init__(self, parent, id)
        self.camera = camera
        self.cap = highgui.cvCreateCameraCapture(camera)
        wximg = wx.Image('resources/icons/camera-error-128.png')
        self.errorBitmap = wximg.ConvertToBitmap()
        self._error = 0
        self.Bind(wx.EVT_IDLE, self.onIdle)

    def onIdle(self, event):
        """
        Event to grab and display a frame from the camera. (internal use).
        """
        if self.cap == None: #Should be cvCameraCapture instance.
            #unbind the idle instance, change to click.
            highgui.cvReleaseCapture(self.cap)  #release the old instance and
            self.cap = highgui.cvCreateCameraCapture(self.camera) #try new one.
            self.displayError(self.errorBitmap, (128, 128))
            raise CameraError('Unable to open camera, retrying....')
            event.Skip()
        try:
            img = highgui.cvQueryFrame(self.cap)
        except cv2.error as e:
            raise CameraError('Error when querying for frame: {0}'.format(e))
        self._error = 0  #worked successfully
        img = opencv.cvGetMat(img)
        cv.cvCvtColor(img, img, cv.CV_BGR2RGB)
        self.displayImage(img)
        event.RequestMore()

    def open(self, camera=-1):
        """
        Open a capture device after __init__ has been called.  Call close() first
        before opening a new device.  Takes camera index as an option.
        """
        self.cap = highgui.cvCreateCameraCapture(camera)
        self.Bind(wx.EVT_IDLE, self.onIdle)
        pass

    def close(self):
        """
        Close a capture device and stops writing frames to the screen.
        """
        highgui.cvReleaseCapture(self.cap)
        self.Unbind(wx.EVT_IDLE)

    def suspend(self):
        """
        Suspend writing frames to the screen.  Should be called when widget is hidden
        to prevent excessive CPU usage.
        """
        self.Unbind(wx.EVT_IDLE)

    def resume(self):
        """
        Resume reading and outputting frames.
        """
        self.Bind(wx.EVT_IDLE, self.onIdle)

    def displayImage(self, img, offset=(0,0)):
        """
        Internal function for writing a bitmap grabbed from OpenCV to the panel.
        """
        bitmap = wx.BitmapFromBuffer(img.width, img.height, img.imageData)
        dc = wx.ClientDC(self)
        dc.DrawBitmap(bitmap, offset[0], offset[1], False)

    def displayError(self, bitmap, offset=(0,0)):
        """
        Shows an error message saying the video device was not found.
        Accepts bitmap as wx.Bitmap and position.  Optimized for 128x128.
        """
        #FIXME: (Minor) a bit of flicker on the error message.
        if self._error > 2: #Only redraw if needed.
            self.Unbind(wx.EVT_IDLE)
            self.Unbind(wx.EVT_LEFT_UP) #just in case
            self.Bind(wx.EVT_LEFT_UP, self.onClick)
            return 0
        boldfont = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
        boldfont.SetWeight(wx.BOLD)
        boldfont.SetPointSize(16)

        dc = wx.ClientDC(self)
        dc.Clear()
        pencolour = wx.Colour(180, 0, 0, wx.ALPHA_OPAQUE)
        brushcolour = wx.Colour(180, 0, 0, wx.ALPHA_OPAQUE)
        dc.SetPen(wx.Pen(pencolour))
        dc.SetBrush(wx.Brush(brushcolour))
        rect = wx.Rect(0,0, 450, 200)
        rect.SetPosition((100, 100))
        dc.DrawRoundedRectangleRect(rect, 8)

        message = 'Unable to open video device.\nIs there one connected?\n\n' \
            'Click here to retry.'
        dc.SetTextForeground('white')
        dc.DrawText(message, 280, 170)
        dc.SetFont(boldfont)
        dc.DrawText('Error', 280, 140)

        dc.DrawBitmap(bitmap, offset[0], offset[1], False)
        self._error += 1

    def onClick(self, event):
        self._error = 1 #For some reason it'll dissapear otherwise.
        self.displayError(self.errorBitmap, (128, 128))
        self.Unbind(wx.EVT_LEFT_UP)
        self.open(self.camera)

    def save(self, file='out'):
        """
        Captures and saves a frame.  Pass the file name to save as.
        Filetype is determined from extension (JPG if none specified).
        """
        img = highgui.cvQueryFrame(self.cap)
        img = opencv.cvGetMat(img)
        #No BGR => RGB conversion needed for PIL output.
        pil = opencv.adaptors.Ipl2PIL(img)  #convert to a PIL
        try:
            pil.save(file)
        except KeyError:
            pil.save(file+'.jpg')


t_CONTROLS_PLAY = wx.NewEventType()
CONTROLS_PLAY = wx.PyEventBinder(t_CONTROLS_PLAY, 1)
t_CONTROLS_STOP = wx.NewEventType()
CONTROLS_STOP = wx.PyEventBinder(t_CONTROLS_STOP, 1)

class Controls(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # Controls
        self.button_play = wx.Button(self, label="Take Picture", size=(140, 50))
        self.button_stop = wx.Button(self, label="Cancel", size=(140, 50))
        self.button_file = wx.Button(self, label="Pick File...", size=(290, 30))

        # Sizers
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.button_play, 0, wx.ALL, border=5)
        sizer.Add(self.button_stop, 0, wx.ALL, border=5)

        bsizer = wx.BoxSizer(wx.VERTICAL)
        bsizer.Add(sizer)
        bsizer.Add(self.button_file, 0, wx.ALL, border=5)

        csizer = wx.BoxSizer(wx.HORIZONTAL)
        csizer.AddStretchSpacer()
        csizer.Add(bsizer)
        csizer.AddStretchSpacer()
        self.SetSizer(csizer)

        # Events
        self.button_play.Bind(wx.EVT_BUTTON, self.Snapshot)
        self.button_stop.Bind(wx.EVT_BUTTON, self.OnStop)

    def Snapshot(self, evt):
        evt2 = wx.PyCommandEvent(t_CONTROLS_PLAY, self.GetId())
        self.GetEventHandler().ProcessEvent(evt2)
        evt.Skip()

    def OnStop(self, evt):
        #close
        evt2 = wx.PyCommandEvent(t_CONTROLS_STOP, self.GetId())
        self.GetEventHandler().ProcessEvent(evt2)
        evt.Skip()

class Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # Controls
        self.live = LivePanel(self, -1) #TODO: Read input number from config
        self.controls  = Controls(self)

        # Sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.live, 1, wx.RIGHT|wx.EXPAND, 4)
        sizer.Add(self.controls, 0, wx.ALL|wx.EXPAND, 4)
        self.SetSizer(sizer)

        # Events
        self.controls.Bind(CONTROLS_PLAY, self.OnPlay)
        self.controls.Bind(CONTROLS_STOP, self.OnStop)

        self.controls.SetBackgroundColour('#005889')
        self.live.SetBackgroundColour('#005889')

        self.toggle = 0

    def OnPlay(self, evt):
        self.live.save()

    def OnStop(self, evt):
        if self.toggle:
            self.live.resume()
            self.controls.button_stop.SetLabel('Suspend')
        else:
            self.live.suspend()
            self.controls.button_stop.SetLabel('Resume')
        self.toggle = not self.toggle
        #self.input_viewer.stop()

class CameraError(Exception):
    def __init__(self, value=''):
        if value == '':
            self.error = 'Generic camera error.'
        else:
            self.error = value
    def __str__(self):
        return repr(self.error)


app = wx.PySimpleApp()
pFrame = wx.Frame(None, -1, "Webcam Viewer", size = (640, 560))
Panel(pFrame)
pFrame.Show()
app.MainLoop()
