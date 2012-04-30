#!/usr/bin/env python
#-*- coding:utf-8 -*-

#TODO: Read config, optionally disable rectangle.
#TODO: Create Destroy() method
#TODO: Implement file system organization, handle converting & uploading image to server.
#TODO: Use gstreamer for Linux instead of opencv - better performance(?)

import os
import wx
import wx.lib.imagebrowser as ib
from cv import RGB as cvRGB
from opencv import cv, highgui
import logging
import opencv

class LivePanel(wx.Panel):
    """
    Creates a  wxPanel for capturing from an USB webcam with OpenCV, meaning
    this works with all platforms OpenCV works with (Linux, OS X, Windows).

    Initialize just like a wx.Panel, optionally specifying a camera index, starting
    from 0.  Default of -1 will automatically select the first useable device.
    """
    def __init__(self, parent, id, camera=-1):
        wx.Panel.__init__(self, parent, id, style=wx.NO_BORDER)
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
        cv.cvRectangle(img, (80, -1), (560, 480), cvRGB(0, 0, 185), 2)
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


t_CONTROLS_SAVE = wx.NewEventType()
CONTROLS_SAVE = wx.PyEventBinder(t_CONTROLS_SAVE, 1)
t_CONTROLS_CANCEL = wx.NewEventType()
CONTROLS_CANCEL = wx.PyEventBinder(t_CONTROLS_CANCEL, 1)
t_CONTROLS_SELECT_FILE = wx.NewEventType()
CONTROLS_SELECT_FILE = wx.PyEventBinder(t_CONTROLS_SELECT_FILE, 1)

class Controls(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # Controls
        self.button_play = wx.Button(self, label="Take Picture", size=(140, 50))
        self.button_cancel = wx.Button(self, label="Cancel", size=(140, 50))
        self.button_file = wx.Button(self, label="Pick File...", size=(290, 30))

        # Sizers
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.button_play, 0, wx.ALL, border=5)
        sizer.Add(self.button_cancel, 0, wx.ALL, border=5)

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
        self.button_cancel.Bind(wx.EVT_BUTTON, self.OnCancel)
        self.button_file.Bind(wx.EVT_BUTTON, self.OnFile)

    def Snapshot(self, evt):
        evt2 = wx.PyCommandEvent(t_CONTROLS_SAVE, self.GetId())
        self.GetEventHandler().ProcessEvent(evt2)
        evt.Skip()

    def OnCancel(self, evt):
        evt2 = wx.PyCommandEvent(t_CONTROLS_CANCEL, self.GetId())
        self.GetEventHandler().ProcessEvent(evt2)
        evt.Skip()

    def OnFile(self, evt):
        evt2 = wx.PyCommandEvent(t_CONTROLS_SELECT_FILE, self.GetId())
        self.GetEventHandler().ProcessEvent(evt2)
        evt.Skip()


class Panel(wx.Panel):
    def __init__(self, parent):
        """
        This is the master webcam capture panel.
        """
        self.log = logging.getLogger(__name__)

        wx.Panel.__init__(self, parent, style=wx.NO_BORDER)
        self.log.debug('Created webcam capture panel.')

        # Controls
        self.log.debug('Using OpenCV device -1')
        self.live = LivePanel(self, -1) #TODO: Read input number from config
        self.controls  = Controls(self)

        # Sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.live, 1, wx.RIGHT|wx.EXPAND, 4)
        sizer.Add(self.controls, 0, wx.ALL|wx.EXPAND, 4)
        self.SetSizer(sizer)

        # Events
        self.controls.Bind(CONTROLS_SAVE, self.OnSave)
        self.controls.Bind(CONTROLS_CANCEL, self.OnStop)
        self.controls.Bind(CONTROLS_SELECT_FILE, self.OnFile)

        self.controls.SetBackgroundColour('#005889') #TODO: source colours from theme.
        self.live.SetBackgroundColour('#005889')
        self.SetBackgroundColour('#005889')

    def OnSave(self, evt):
        self.live.save()

    def OnStop(self, evt):
        """
        Hides the panel and suspends video input.
        """
        self.log.debug('Hide webcam panel.')
        self.Hide()
        self.live.suspend()
        evt.Skip()

    def OnFile(self, evt):
        """
        Internal event for the CONTROLS_SELECT_FILE event.
        Read the selection with GetFile().
        """
        self.live.suspend()
        initial_dir = os.getcwd()
        dlg = ib.ImageDialog(self, initial_dir)
        dlg.Centre()

        #TODO: Process file selection
        if dlg.ShowModal() == wx.ID_OK:
            # show the selected file
            self.fileSelection = dlg.GetFile()
        else:
            self.fileSelection = None

        dlg.Destroy()
        self.live.resume()

    def GetFile(self):
        """
        Retrieve the file selected by the user after the
        CONTROLS_SELECT_FILE event.
        """
        return self.fileSelection

class CameraError(Exception):
    def __init__(self, value=''):
        if value == '':
            self.error = 'Generic camera error.'
        else:
            self.error = value
    def __str__(self):
        return repr(self.error)


if __name__ == '__main__':
    app = wx.PySimpleApp()
    pFrame = wx.Frame(None, -1, "Webcam Viewer", size = (640, 560))
    Panel(pFrame)
    pFrame.Show()
    app.MainLoop()
