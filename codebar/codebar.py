#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
Generates and crops barcodes. Use code.gen("code39", "file.png", "HELLO")
to save a cropped barcode to file.png.  (only PNG is implemented so far).

Couldn't figure out how to pass image size to pybarcode, so it'll be done
with PIL.  This'll also contain methods for generating QR codes, etc.
(probably has something to do with quiet_zone, but we'd like to crop
out the subtext.  (http://packages.python.org/pyBarcode/writers/index.html)
Supported symbologies should at least support uppercase ASCII.

Uses pybarcode (2.7.1 distribution), David Jane's fork of QRCode for python
(pyqrcode.py, MIT), and Jostein Leira's Code128 implementation (code128.py)
"""

codes = ['qr', 'code39', 'code128'] # working/supported codes

import os
import Image
import pyqrcode
import barcode
from barcode.writer import ImageWriter
from code128 import Code128

def gen(encoding, fileName, text, width=300, height=100):
    """Returns 0 success; all else are errors.
    gen(encoding, fileName, text, width=300, height=100)
    note: geometry settings only valid for code128.
    """

    if encoding not in codes:
        raise NotImplementedError("Unsupported encoding")
        return 2

    if encoding == 'qr':
        #generate QR code
        qr_image = pyqrcode.MakeQRImage(text, br = True)
        fileHandle = file(fileName, 'w')
        qr_image.save(fileHandle, 'PNG')
        fileHandle.close()
        return 0

    elif encoding == 'code128':
        #generate using Code128() by Jostein Leira
        bar = Code128()
        bar.getImage(text, fileName, 300, 100)
        return 0

    else:
        #generate barcode
        pre = barcode.get_barcode(encoding, text, writer=ImageWriter())
        save = pre.save(fileName)

        out = Image.open(save)
        #crop the image
        if encoding == 'code39':
            out = out.crop((28, 10, out.size[0]-24, 180))
        os.unlink(save)
        fileHandle = file(fileName, 'w')
        out.save(fileHandle, 'PNG')
        fileHandle.close()
        return 0


def supported():
    """Returns supported barcode types in a list."""
    return codes

if __name__ == '__main__':
    gen('code128', 'test128.png', '5c55')
    #gen('code39', 'test39.png', 'testing')
    #gen('qr', 'testQR.png', 'testing')
