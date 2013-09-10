#!/usr/bin/env python
#-*- coding:utf-8 -*-

#TODO:  Update for use with new API
#TODO: Read config, optionally disable rectangle.
#TODO: Create Destroy() method
#TODO: Implement file system organization, handle converting & uploading image to server.
#TODO: Use gstreamer for Linux instead of opencv - better performance(?)

#This is needed for PIL to import in OS X (FIXME)
import sys
sys.path.append('/opt/local/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/site-packages')

import os
import wx
import wx.lib.imagebrowser as ib
import logging
import conf
from itertools import *
from operator import itemgetter
from PIL import Image

if conf.as_bool(conf.config['webcam']['enable']):
    import opencv
    from opencv import cv, highgui

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
        self.store = Storage()
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
        if conf.as_bool(conf.config['webcam']['cropBars']):
            #Draw cropping region
            cv.cvRectangle(img, (80, -1), (560, 480), (205.0, 0.0, 0.0, 0.0), 2)
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

    def save(self, record=-1):
        """
        Captures, crops, and saves a webcam frame.  Pass an explicit record number
        otherwise writes to next in sequence.  Returns zero-padded photo reference ID.
        """
        img = highgui.cvQueryFrame(self.cap)
        img = opencv.cvGetMat(img)
        #No BGR => RGB conversion needed for PIL output.
        pil = opencv.adaptors.Ipl2PIL(img)  #convert to a PIL
        #~ pil = pil.crop((80, 0, 560, 480))
        #~ pil.show()

        return self.store.savePIL(pil, record)
        #~ try:
            #~ pil.save(file)
        #~ except KeyError:
            #~ pil.save(file+'.jpg')

class Storage:
    """
    Crops, resizes, stores, and retrieves images for the database.
    """
    def __init__(self):
        self.log = logging.getLogger(__name__)
        #~ self.log.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(asctime)s] %(module)-6s  [%(levelname)-8s]  %(message)s')
        ch.setFormatter(formatter)
        self.log.addHandler(ch)

        self.log.debug("Created webcam storage instance.")

        store = conf.config['webcam']['store'].lower()
        if store == 'local':
            self.log.debug("Configured for local storage.")
            self.store = 'local'
            olddir = os.getcwd()
            os.chdir(os.path.join(conf.homepath, '.taxidi'))
            self.target = os.path.abspath(conf.config['webcam']['target'])
            self.thumbs = os.path.abspath(conf.config['webcam']['thumbs'])
            os.chdir(olddir)  #Switch back to old cwd

            #See if target directories exist, and create if needed.
            for target in [self.target, self.thumbs]:
                if not os.path.exists(target):
                    #Doesn't exist, try to create:
                    self.log.warn("Directory {0} doesn't exist. Attempting to create...".format(target))
                    try:
                        os.makedirs(target)
                    except error as e:
                        self.log.error(e)
                        self.log.error("Directory already exists or permission denied when creating directory.")
                        raise

            self.log.debug("Target: {0}".format(self.target))
            self.log.debug("Thumbs: {0}".format(self.thumbs))

        elif store == 'remote':
            self.store = 'remote' #TODO remote storage (low priority)

    def savePIL(self, image, record=-1):
        """
        Saves an image in PIL format, cropping & resizing if needed, and creating
        a thumbnail.
        `image`: A valid PIL instance.
        `record`: Explicit id (integer) to save the image to (as a reference).

        All other values are determined from [webcam] section in config.
        If record is -1, the id will be automatically determined by the first
        available slot.  Returns zero-padded ID as string.
        """

        if ((image.size[0] != 640) and (image.size[1] != 480)) or \
           ((image.size[0] != 480) and (image.size[1] != 480)):
            #Scale up/down:
            print "Scale"
            image.thumbnail((480, 480))

        if image.size != (480, 480):
            #Crop it down.
            print "Crop"
            image = image.crop((80, 0, 560, 480))

        if record >= 0: #Explicit file
            record = str(record).zfill(6)
        else:  #Determine automatically
            record = str(self._getNextSlot()).zfill(6)

        filename = os.path.join(self.target, record + '.jpg')
        self.log.debug("Saving image as {0}...".format(filename))
        try:
            image.save(filename)
        except:
            self.log.error("Unable to save image!")
            raise

        #Create & save thumbnails:
        image.thumbnail((128, 128))
        filename = os.path.join(self.thumbs, record + '.jpg')
        try:
            image.save(filename)
        except:
            self.log.error("Unable to save image!")
            raise

        return record

    def getThumbnail100(self, record):
        """
        Returns a 100x100 wxBitmap given a record number.
        """
        pil = Image.open(self.getThumbnailPath(record))
        pil.thumbnail((100, 100))
        image = wx.EmptyImage(*pil.size)
        image.SetData(pil.convert("RGB").tostring())
        return wx.BitmapFromImage(image)

    def saveImage(self, filename, record=-1):
        """
        Like savePIL(), but accepts local filename as argument instead.
        Used for inserting a custom image into the photo database.
        """
        try:
            image = Image.open(filename)
        except IOError as e:
            self.log.error(e)
            self.log.error('Unable to copy image.')
            raise

        #From a webcam most likely:
        if image.size == (640, 480):
            image = image.crop((80, 0, 560, 480))

        #Scale to fit
        image.thumbnail((480, 480), Image.ANTIALIAS)


        if record >= 0: #Explicit file
            record = str(record).zfill(6)
        else:  #Determine automatically
            record = str(self._getNextSlot()).zfill(6)

        filename = os.path.join(self.target, record + '.jpg')
        self.log.debug("Saving image as {0}...".format(filename))
        try:
            image.save(filename)
        except:
            self.log.error("Unable to save image!")
            raise

        #Create & save thumbnails:
        image.thumbnail((128, 128), Image.ANTIALIAS) #User higher quality for custom images
        filename = os.path.join(self.thumbs, record + '.jpg')
        try:
            image.save(filename)
        except:
            self.log.error("Unable to save image!")
            raise

        return record


    def delete(self, record):
        try:
            os.unlink(self.getImagePath(record))
            os.unlink(self.getThumbnailPath(record))
        except OSError as e:
            self.log.error(e)
            self.log.error("Unable to unlink files for photo record {0}".format(record))


    def _getNextSlotAdvanced(self):  #FIXME
        files = []
        ret = []
        for dirname, dirnames, filenames in os.walk(self.target):
            for name in filenames:
                files.append(int(name.strip('.jpg')))
        files.sort()
        for k, g in groupby(enumerate(files), lambda (i, x): i - x):
            ret.append(map(itemgetter(1), g))
        return int(ret[1][-1]) + 1

    def _getNextSlot(self):
        files = []
        for filename in os.listdir(self.target):
            if filename.endswith('.jpg'):
                files.append(int(filename.strip('.jpg')))
        files.sort()
        if len(files) == 0:
            return 0
        return int(files[-1]) + 1




    def getImagePath(self, record):
        """
        Returns the full file path for a photo record (local).
        """
        try:
            return os.path.join(self.target, str(int(record)).zfill(6) + '.jpg')
        except ValueError:
            return None

    def getThumbnailPath(self, record):
        """
        Returns full file path for a photo record thumbnail (local).
        """
        return os.path.join(self.thumbs, str(int(record)).zfill(6) + '.jpg')




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
        device = int(conf.config['webcam']['device'])
        self.log.debug('Using OpenCV device {0}'.format(device))
        self.live = LivePanel(self, device)
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

        #Variables:
        self.overwrite = None

        #Storage instance:
        self.PhotoStorage = Storage()


    def OnSave(self, evt):
        """
        Internal event for saving an image from the webcam.
        Read the reference ID with GetFile().
        """
        if self.overwrite != None:
            self.fileSelection = self.live.save(self.overwrite)
        else:
            self.fileSelection = self.live.save()
        self.overwrite = None
        evt.Skip()

    def SetOverwrite(self, record):
        self.overwrite = record

    def OnStop(self, evt):
        """
        Hides the panel and suspends video input.
        """
        self.log.debug('Hide & suspend webcam panel.')
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
            evt.Skip()
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
        
def getVideoDevices():
    """
    Returns a list of available system video devices by name.
    Pass index of this list to video capture class to use that device
    (Linux only) or pass -1 to use the first available video device.
    
    Note that this may have issues on some implementations of OpenCV.
    """
    
    try:
        import subprocess
        devices = subprocess.check_output(
            'for I in /sys/class/video4linux/*; do cat $I/name; done', 
            shell=True)
    except AttributeError:
        #Python < 2.7, use os.popen instead.
        fdev = os.popen('for I in /sys/class/video4linux/*; do cat $I/name; done')
        devices = fdev.read()
        fdev.close()
        
    #Cast to list and
    devices = devices.split('\n')[:-1] #Remove trailing \n
    return devices



if __name__ == '__main__':
    import opencv
    from opencv import cv, highgui
    app = wx.PySimpleApp()
    pFrame = wx.Frame(None, -1, "Webcam Viewer", size = (640, 560))
    Panel(pFrame)
    pFrame.Show()
    app.MainLoop()
