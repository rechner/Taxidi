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
import math
import zlib
import base64

directions = [bin(0x7070563)[2:][i:i+3] for i in range(0,27,3)]

def encode(lines):
    if len(lines) == 0: return '0'
    
    # check if 3 points are on the same line, in order
    def ison(a, c, b):
      within = lambda p, q, r: p <= q <= r or r <= q <= p
      return ((b[0] - a[0]) * (c[1] - a[1]) == (c[0] - a[0]) * (b[1] - a[1])
        and (within(a[0], c[0], b[0]) if a[0] != b[0] else 
          within(a[1], c[1], b[1])))
    
    # converts series of lines to 'connect the dots', and looks for single dots
    strokes = [[lines[0][0:2]]]; dots = []
    for line in lines:
      if line[0:2] != strokes[-1][-1]: 
        if len(strokes[-1]) == 1:
          dots += strokes.pop()
        strokes += [[line[0:2]]]
      if line[2:4] != strokes[-1][-1]:
        if len(strokes[-1]) > 1 and \
          ison(strokes[-1][-2], strokes[-1][-1], line[2:4]):
            strokes[-1][-1] = line[2:4]
        else:
          strokes[-1] += [line[2:4]]
    if len(strokes[-1]) == 1:
      dots += strokes.pop()
    
    # big endian, most significant first
    def BEVLI4Enc(num):
      if num == 0: return '0' * 4
      else:
        temp = -(-int(math.log(num, 2) + 1) // 3) * 3
        temp = [bin(num)[2:].zfill(temp)[i:i+3] for i in range(0, temp, 3)]
        return '1'.join([''] + temp[:-1]) + '0' + temp[-1]
    
    # encode dots in binary
    data = ''.join(map(BEVLI4Enc, [len(dots)] + [i for d in dots for i in d]))
    
    # convert series of points to deltas, then convert to binary
    for stroke in strokes:
      prev_point = stroke[0]
      data += ''.join(map(BEVLI4Enc, (len(stroke) - 2,) + prev_point))
      for point in stroke[1:]:
        dx, dy = point[0] - prev_point[0], point[1] - prev_point[1]
        prev_point = point
        # format: bit 'is this delta more than 1 pixel?', 3xbits direction
        # directions:   111   000   001
        #               110    #    010
        #               101   100   011
        isleap = abs(dx) > 1 or abs(dy) > 1
        data += ('1' if isleap else '0') + \
          directions[cmp(dx, 0) + 1 + (cmp(dy, 0) + 1) * 3]
        if isleap:
          if abs(dx): data += BEVLI4Enc(abs(dx))
          if abs(dy): data += BEVLI4Enc(abs(dy))
    
    # pad to byte boundry, then convert to binary
    data = ''.join(map(lambda x: chr(int(x, 2)), \
      [data[i:i+8].ljust(8, '0') for i in range(0,len(data),8)]))
    
    # base 95 encoder
    def b95btoa(b):
      b95 = ''; n = int(('_' + b).encode('hex'), 16)
      while n > 0:
        b95 += chr(int(n % 95 + 32)); n /= 95
      return b95[::-1]
    
    # compress using zlib if it makes it smaller
    z = zlib.compress(data)[2:-4]
    if len(z) < len(data):
      return 'c' + b95btoa(z)
    else:
      return 'e' + b95btoa(data)

def decode(data):
    if data[0] == '0': return []
    
    # dewrapper functions
    def inflate(z):
      return zlib.decompress(z, -zlib.MAX_WBITS)
    def b64atob(b64):
      return base64.b64decode(b64 + '=' * (4 - len(b64) % 4))
    def b95atob(b95):
      n = 0; m = 1
      for c in b95[::-1]:
        n += (ord(c) - 32) * m; m *= 95
      return hex(n)[4:-1].decode('hex')
    def unwrap(d):
      return {
        'a': inflate,                       # zlib compression
        'b': lambda x: x,                   # raw version 1 format
        'c': lambda x: inflate(b95atob(x)), # base 95 encoding, zlib compression
        'd': lambda x: inflate(b64atob(x)), # base 64 encoding, zlib compression
        'e': b95atob,                       # base 95 encoding, no compression
        'f': b64atob                        # base 64 encoding, no compression
      }[d[0]](d[1:])
     
    # unwrap, break into groups of 4, and convert to 01
    data = ''.join([bin(ord(c))[2:].rjust(8, '0') for c in unwrap(data)])
    data = [data[i:i+4] for i in range(0, len(data), 4)]
    
    def BEVLI4Dec(arr):
      temp = [arr.pop(0)]
      while temp[-1][0] == '1':
        temp += [arr.pop(0)]
      return int(''.join([i[1:4] for i in temp]), 2)
    
    #decode dots
    lines = []
    for d in range(0, BEVLI4Dec(data)):
      x, y = BEVLI4Dec(data), BEVLI4Dec(data)
      lines += [(x, y, x, y)]
    
    #decode strokes
    num_points = BEVLI4Dec(data)
    while num_points > 0:
      last_line = (0, 0, BEVLI4Dec(data), BEVLI4Dec(data))
      for i in range (0, num_points + 1):
        isleap = data[0][0] == '1'
        direction = directions.index(data.pop(0)[1:4])
        dx, dy = direction % 3 - 1, direction / 3 - 1
        last_line = (last_line[2], last_line[3], 
          last_line[2] + dx * (BEVLI4Dec(data) if isleap and dx != 0 else 1),
          last_line[3] + dy * (BEVLI4Dec(data) if isleap and dy != 0 else 1))
        lines += [last_line]
      num_points = BEVLI4Dec(data) if len(data) > 0 else 0
    
    return lines

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
            encoded = encode(self.sigpad.signature)
            print decode(encoded)


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
    



