#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
import conf
import logging
from configobj import ConfigObj
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
from email.Utils import COMMASPACE, formatdate
from email import Encoders

debug = False
global log

def send(to, fromText, subject, text, html='', images=[]):
    fromaddr = conf.config['report']['email']['from']
    if html == '':
        html = "<html><body>{}</body></html>".format(text.replace('\n', '<br>'))

    #See http://code.activestate.com/recipes/473810/ for details
    #Construct the message:
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = '{0} <{1}>'.format(fromText, conf.config['report']['email']['from'])
    msg['To'] = to
    msg.preamble = 'This is a multi-part message in MIME format.'

    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they want to display.
    msgAlternative = MIMEMultipart('alternative')
    msg.attach(msgAlternative)

    msgText = MIMEText(text)
    msgAlternative.attach(msgText)

    msgText = MIMEText(html, 'html')
    msgAlternative.attach(msgText)

    #Attach images with proper references
    for i in images:
        msgImage = MIMEImage(i[i.keys()[0]])
        # Define the image's ID as referenced above
        msgImage.add_header('Content-ID', '<{0}>'.format(i.keys()[0]))
        msg.attach(msgImage)

    #Send the message:
    log.info("Attempting to send email to recipient {0}...".format(to))
    try:
        server = smtplib.SMTP(conf.config['report']['email']['host'])
    except smtplib.SMTPConnectError as e:
        log.error("Unable to connect to SMTP server.")
        log.error(e)
        raise

    if conf.as_bool(conf.config['report']['email']['TLS']):
        server.starttls()

    try: #Send HELO
        server.ehlo()
    except smtplib.SMTPHeloError as e:
        log.error("Server refused our HELO message.")
        log.error(e)
        raise

    try:
        server.login(conf.config['report']['email']['user'], conf.config['report']['email']['pass'])
    except smtplib.SMTPAuthenticationError as e:
        log.error("Email authentication failure.")
        log.error(e)
        raise

    try:
        server.sendmail(fromaddr, to, msg.as_string())
    except smtplib.SMTPResponseException as e:
        log.error("SMTP server returned error code {0}: {1}".format(e.smtp_code, e.smtp_error))
        log.error(e)
        raise
    except smtplib.SMTPException as e:
        log.error("Unknown SMTP error occurred.")
        log.error(e)
        raise
    except:
        log.error("Unexpected error when sending email.")
        raise

    log.info("Email sent successfully.")
    server.quit()


def register(to, template):
    try:
        dat = readTemplate(template)
    except:
        #Use defaults
        dat = {'register': {'subject': 'Welcome!', 'text': 'welcome.txt',
                            'html': 'welcome.html', 'images': 'banner.jpg'}
              }

    section = dat['register']

    #Read in the file contents
    f = open(os.path.join('resources', 'email', section['text']))
    text = f.read()
    f.close()

    f = open(os.path.join('resources', 'email', section['html']))
    html = f.read()
    f.close()

    #Read in images:
    images = []
    for i in section['images']:
        f = open(os.path.join('resources', 'email', i))
        images.append({ i.split('.')[0] : f.read() })
        f.close()

    send(to, section['from'], section['subject'], text, html, images)

def readTemplate(template):
    path = os.path.join('resources', 'email', template + '.conf')
    try:
        f = open(path)
    except IOError:
        raise #Couldn't open template

    return ConfigObj(path)

def _setupLogging():
    global log
    log = logging.getLogger(__name__)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s] %(module)-6s  [%(levelname)-8s]  %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)

_setupLogging()

if __name__ == '__main__':
    debug = True
    log.setLevel(logging.DEBUG)
    register('journeytaxidi@googlemail.com', 'default')
