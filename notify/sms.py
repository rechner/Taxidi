#!/usr/bin/env python
#-*- coding:utf-8 -*-

#master class for sending SMS alerts (currently only through google voice).
#see README.gv for more information.

class SMS:
    def __init__(self, notifyEnable=False, driver='gvoice', user=None, passwd=None):
        """
        Note: Due to the time it takes to complete a login to Google Voice, this
        class should always be called in its own thread to keep the UI active.
        """
        if notifyEnable:
            import local as notify
        else:
            import local.Dummy as notify #Supress notifications
        self.notify = notify

        if driver == 'gvoice':
            self.device = GoogleVoice(user, passwd)

    def send(self, number, text):
        """
        Sends a message using the initialized SMS driver.
        """
        self.device.send(number, text)
        self.notify.info("SMS Alert Sent", "Message sent to {0}".format(number))

    def sendMany(self, numbers, text):
        """
        Send the same message to multiple recipients (in a list).
        """
        for number in numbers:
            self.device.send(number, text)

        self.notify.info("SMS Alert Sent", "Message sent to\n{0}".format(
            ", \n".join(map(str, numbers[:-1])) + " and " + numbers[-1] + "."))

class GoogleVoice:
    def __init__(self, user=None, passwd=None):
        from googlevoice import Voice
        from googlevoice import util

        self.voice = Voice()
        try:
            self.voice.login(user, passwd)
        except util.LoginError:
            raise LoginError

    def send(self, number, text):
        """
        Sends a message to a number in any standard format.
        (e.g. 4803335555, (480) 333-5555, etc.)
        """
        self.voice.send_sms(number, text)


class LoginError(Exception):
    """
    Occurs when login credentials are incorrect.
    """


if __name__ == '__main__':
    sms = SMS(notifyEnable = True, user='journeytaxidi', passwd='aRY0VtKfhXtDDZeLbXTu')
    sms.send(u"(317) 455-5832", "Mew")
