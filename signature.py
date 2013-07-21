#!/usr/bin/env python
#*-* coding:utf-8 *-*
# signature.py © 2012 Zac Sturgeon and Nathan Lex

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#       
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#       
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.


"""
A simple free-drawing area which outputs the drawing as a list
of line segments, suitable for capturing signatures to store in a
database.  The module includes an optimised compression algorithm
with a 92% compression ratio.

See http://jkltech.net/taxidi/wiki/Signature_Format
"""

__version__ = '0.1'
__all__ = ['SignaturePad']

import wx

class SignaturePad(wx.Window):
    """Widget for drawing and capturing a signature.
       Optimised for a size of 500 x 200."""
    
    def __init__(self, parent, signatureLine=True, 
            signatureLineText='Sign Here', signatureLineColour='Grey'):
        super(SignaturePad, self).__init__(parent,
            style=wx.NO_FULL_REPAINT_ON_RESIZE)
        self._initDrawing()
        self._bindEvents()
        self._initBuffer()
        self.signature = []
        self.debug = False #Set to true to enable debugging output
        self.signatureLine = signatureLine
        self.signatureLineText = signatureLineText
        self.signatureLineColour = signatureLineColour
        self.SetMinSize((500, 200))
        self.SetMaxSize((500, 200))
        
    def _initDrawing(self):
        self.SetBackgroundColour('White')
        self.penThickness = 2      #default pen thickness
        self.penColour = '#145394' #default colour
        self.lines = []
        self.previousPosition = (0, 0)
        
    def _bindEvents(self):
        for event, handler in [ \
                (wx.EVT_LEFT_DOWN, self.onLeftDown), # Start drawing
                (wx.EVT_LEFT_UP, self.onLeftUp),     # Stop drawing 
                (wx.EVT_MOTION, self.onMotion),      # Draw
                (wx.EVT_SIZE, self.onSize),          # Prepare for redraw
                (wx.EVT_IDLE, self.onIdle),          # Redraw
                (wx.EVT_PAINT, self.onPaint),        # Refresh
                (wx.EVT_WINDOW_DESTROY, self.cleanup)]:
            self.Bind(event, handler)
            
    def _initBuffer(self):
        # Initialize the bitmap used for the display buffer
        size = self.GetClientSize()
        self.buffer = wx.EmptyBitmap(size.width, size.height)
        dc = wx.BufferedDC(None, self.buffer)
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()
        self.drawLines(dc, *self.lines)
        self.reInitBuffer = False  #set flag
        
    def SetPenColour(self, colour):
        """Sets the active pen colour. Returns true if changed."""
        if (self.penColour == colour): return False
        self.penColour = colour
        return True
        
    def SetPenThickness(self, thickness):
        """Sets the pen thickness."""
        self.penThickness = thickness


    #Event handlers:
    def onLeftDown(self, event):
        """Called on left button press (pen down)"""
        self.currentLine = []
        self.previousPosition = event.GetPositionTuple()
        self.CaptureMouse()
        
    def onLeftUp(self, event):
        """Called on left button release (pen up)"""
        if self.HasCapture():
            self.lines.append((self.penColour, self.penThickness,
                self.currentLine))
            self.currentLine = []
            self.ReleaseMouse()
            
    def onMotion(self, event):
        """Called when the mouse moving (pen is being dragged). If the
           left button is down while dragging, a line is drawn from the
           last event position to the new one.  Coordinates are saved
           for redrawing and appended to the signature output."""
        if event.Dragging() and event.LeftIsDown():
            dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
            currentPosition = event.GetPositionTuple()
            lineSegment = self.previousPosition + currentPosition
            self.signature.append(lineSegment) #Store signature value
            self.drawLines(dc, (self.penColour, self.penThickness,
                [lineSegment]))
            self.currentLine.append(lineSegment)
            self.previousPosition = currentPosition
            
            if self.debug:
                print self.signature
                print len(self.signature)
                
    def onSize(self, event):
        """Enables flag to cause a redraw event if the window is 
           resized"""
        self.reInitBuffer = True
    
    def onIdle(self, event):
        """If the window is resized, the bitmap is recopied to match
           the new window size.  The buffer is re-initialized while
           idle such that a refresh only occurs once when needed."""
        if self.reInitBuffer:
            self._initBuffer()
            self.Refresh(False)
            
    def onPaint(self, event):
        """Paints window and signature line when exposed."""
        # Create a buffered paint DC.  It will create the real
        # wx.PaintDC and then blit the bitmap to it when dc is
        # deleted.  Since we don't need to draw anything else
        # here that's all there is to it.
        dc = wx.BufferedPaintDC(self, self.buffer)
        
        #Signature line
        if self.signatureLine:
            self.drawLines(dc, (self.signatureLineColour, 
                           2, [(20, 150, 480, 150)]))
            font = wx.Font(10, wx.FONTFAMILY_SCRIPT, 
                        wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
            dc.SetFont(font)
            dc.SetTextForeground(self.signatureLineColour)
            dc.DrawText(self.signatureLineText, 20, 155)
            
    def clear(self):
        self.currentLine = []
        self.signature = []
        self.reInitBuffer = True
        self._initBuffer()
        dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
        dc.Clear()
        self.Refresh()
            
    def cleanup(self, event):
        #for future use
        return True
        
    @staticmethod
    def drawLines(dc, *lines):
        ''' drawLines takes a device context (dc) and a list of lines
        as arguments. Each line is a three-tuple: (colour, thickness,
        linesegments). linesegments is a list of coordinates: (x1, y1,
        x2, y2). '''
        dc.BeginDrawing()
        for colour, thickness, lineSegments in lines:
            pen = wx.Pen(colour, thickness, wx.SOLID)
            dc.SetPen(pen)
            for lineSegment in lineSegments:
                dc.DrawLine(*lineSegment)
        dc.EndDrawing()

        
t_CONTROLS_CANCEL = wx.NewEventType()
CONTROLS_CANCEL = wx.PyEventBinder(t_CONTROLS_CANCEL, 1)
        
class SignaturePadControls(wx.Panel):
    def __init__(self, parent=None):
        super(SignaturePadControls, self).__init__(parent)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        bsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.CancelButton = wx.Button(self, wx.ID_CANCEL, size=(-1, 50))
        self.ClearButton = wx.Button(self, wx.ID_CLEAR, size=(-1, 50))
        self.AcceptButton = wx.Button(self, wx.ID_OK, size=(-1, 50))
        bsizer.Add(self.ClearButton, 1, wx.EXPAND | wx.ALL, 5)
        bsizer.AddStretchSpacer()
        bsizer.Add(self.CancelButton, 1, wx.EXPAND | wx.ALL, 5)
        bsizer.Add(self.AcceptButton, 1, wx.EXPAND | wx.ALL, 5)
        
        self.sigpad = SignaturePad(self)
        sizer.Add(bsizer, 0, wx.EXPAND)
        sizer.Add(self.sigpad, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
        self.CancelButton.Bind(wx.EVT_BUTTON, self.onCancel)
        self.ClearButton.Bind(wx.EVT_BUTTON, self.onClear)
        self.AcceptButton.Bind(wx.EVT_BUTTON, self.onAccept)
        
    def onClear(self, event):
        self.sigpad.clear()
        
    def onCancel(self, event):
        evt2 = wx.PyCommandEvent(t_CONTROLS_CANCEL, self.GetId())
        self.GetEventHandler().ProcessEvent(evt2)
        event.Skip()
        pass
        
    def onAccept(self, event):
        if self.sigpad.signature == []:
            wx.MessageBox('Signature cannot be blank!',
              'Error', wx.OK | wx.ICON_ERROR)
        else:
            print self.sigpad.signature
        
    
        
class TestFrame(wx.Frame):
    def __init__(self, parent=None):
        super(TestFrame, self).__init__(parent, title="Signature Pad",
            size=(500,260),
            style=wx.DEFAULT_FRAME_STYLE^ wx.RESIZE_BORDER)
        
        signature = SignaturePadControls(self)
        signature.Bind(CONTROLS_CANCEL, self.onCancel)
        self.Centre()
        
    def onCancel(self, event):
        self.Close()


if __name__ == '__main__':
    app = wx.App()
    frame = TestFrame()
    frame.Show()
    app.MainLoop()
