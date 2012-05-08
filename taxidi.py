#!/usr/bin/env python
#-*- coding:utf-8 -*-

STATUS_NONE = 0
STATUS_CHECKED_IN = 1
STATUS_CHECKED_OUT = 2

class Error(Exception):
    def __init__(self, code, value=''):
        self.error = value
        self.code = code
    def __str__(self):
        return repr(self.error)
