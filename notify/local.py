#!/usr/bin/env python
#*-* coding:utf-8 *-*

#For showing local libnotify pop-ups, etc.
#TODO: Allow generic toaster pop-up notifications.

#import conf
#enable = conf.as_bool(conf.config['interface']['libnotify'])
enable = True

class Dummy:
    """
    Dummy class to supress notifications with.
    """
    @staticmethod
    def warning(title, message):
        pass
    
    @staticmethod    
    def error(title, message):
        pass 
    
    @staticmethod    
    def info(title, message):
        pass

try:
    import pynotify
    enable = pynotify.init("Taxidi")
except ImportError:
    pass #Use toaster pop-ups

def warning(title, message):
    """
    Shows a warning pop-up notification
    """
    if enable:
        n = pynotify.Notification(title, message, "dialog-warning")
        n.set_timeout(3000) #Don't show it for too long
        n.set_urgency(pynotify.URGENCY_CRITICAL)
        n.show()

def error(title, message):
    if enable:
        n = pynotify.Notification(title, message, "dialog-error")
        n.set_urgency(pynotify.URGENCY_CRITICAL)
        n.show()
        
def info(title, message):
    if enable:
        n = pynotify.Notification(title, message, "dialog-info")
        n.set_urgency(pynotify.URGENCY_NORMAL)
        n.show()

if __name__ == '__main__':
    info("Test", "This is an informational notification.")
