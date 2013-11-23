#!/usr/bin/env python
#-*- coding:utf-8 -*-

# dblib/sqlite.py (spaces, not tabs)
# SQLite3 database driver for Taxídí.
# Zac Sturgeon <admin@jkltech.net>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.

# All database tables and features are documented here:
#   http://jkltech.net/taxidi/wiki/Database

# Coding conventions:
# Functions which are called or initiated from outside this class should
#   use UpperCamelCase only.  Internal functions should at least begin
#   lowercase, and use underscore seperation ( this_for_example() ).
#   All camel case abbreviations should be all capital (StartHTTPServer)
# Note that because SQLite has no bool data type, all booleans must be
#   converted to integers before storing (False=0, True=1)

# NOTE: Since not all versions of sqlite come with forgein key support
#  (Ubuntu 11.04 sqlite 3.7.4 doesn't), all constraints will have to be
#  maintained by this driver (TODO)

#TODO: FORGEIN KEY enforcements

debug = True  #Set to true to enable [very] verbose logging to console

import os
import sys
import logging
import time
import datetime
import sqlite3 as sqlite
import hashlib

# one directory up
_root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, _root_dir)
import taxidi

#Signaling constants
SUCCESS = 1
OK = 1
FAIL = 2
EMPTY_RESULT = 4
USER_EXISTS = 8
CONSTRAINT_FAILED = 16
UNKNOWN_ERROR = 32
AUTHORIZED = 1
UNAUTHORIZED = 0
NEW = 128
RESET_TABLES = 256

#Database schema version (integer):
database_version = 1

class Database:
    """SQLite3 driver class for taxídí database."""
    def __init__(self, file, log=''):
        """
        Open connections to sqlite file; create if it doesn't exist.
        Takes a file and optional logger handler as init arugments.
        """

        self.debug = True
        #what columns will be returned when SELECT * is issued. Keeps things from breaking.
        self.columns = """data.id, data.name, data.lastname, dob, data.activity,
                          data.room, grade, phone, data.mobileCarrier,
                          data.paging, data.parent1, data.parent1Link,
                          data.parent2, data.parent2Link, data.parentEmail,
                          data.medical, data.joinDate, data.lastSeen,
                          data.lastModified, data.count, data.visitor,
                          data.noParentTag, data.barcode, data.picture,
                          data.authorized, data.unauthorized, data.notes"""

        #convert log to global if a handle was passed:
        if log:
            self.log
            self.log = log
        else:
            self.log = logging.getLogger(__name__)
            #~ self.log.setLevel(logging.DEBUG) #Comment out for production
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            formatter = logging.Formatter('[%(asctime)s] %(module)-6s  [%(levelname)-8s]  %(message)s')
            ch.setFormatter(formatter)
            self.log.addHandler(ch)
            if debug:
                self.log.setLevel(logging.DEBUG)

        file = os.path.expanduser(file)
        self.log.debug('Attempting to open sqlite3 database at {0}'.format(file))
        #check if file exists/is readable
        try:
            fh = open(file, 'r')
            fh.close()
            self.status = OK
        except IOError as e:
            try: #Create intermediate directories if needed
                os.makedirs(os.path.dirname(file))
            except OSError as e:
                if e.errno == 17: #Already exists
                    pass
                else:
                    raise
            self.log.warn('({0})'.format(e))
            #file does not exist: Create table
            self.conn = sqlite.connect(file)
            self.conn.text_factory = str #use unicode strings
            self.cursor = self.conn.cursor()
            self.createTables()
            self.conn.commit()
            self.conn.close()
            self.status = NEW

        #check if database can be written to (modification/creation)
        if not os.access(file, os.W_OK):
            self.log.critical(
                'the file {0} does not have write permissions!'.format(file))
            self.log.critical('Unable to open database.')
            return 127 #Causes TypeException in the calling module.

        #open database for writing and query
        self.conn = sqlite.connect(file, check_same_thread = False)
        self.cursor = self.conn.cursor()
        self.log.info("Created sqlite3 database instance using file '{0}'".
            format(file))
        if self.debug:
            self.log.debug("Default cursor instance is: {0}".format(str(self.cursor)))
            
    def spawnCursor(self):
        """
        Returns a new cursor object (for multi-threadding use).
        Delete it when done.
        """
        return self.conn.cursor()

    def close(self):
        self.log.info("Closing database cursor and connection...")
        self.cursor.close()
        self.conn.close()
        del self.cursor
        del self.conn

    def createTables(self):
        """
        Initializes the database, creating required tables.
        """
        self.log.warning('Tables did not exist. Creating...')
        #Set database version:
        #NOTE: No chance of injection here - not an user input.
        self.execute("PRAGMA user_version = {0};".format(database_version))
        #main data
        self.execute("""CREATE TABLE data(id integer primary key,
            name text, lastname text,  dob text, activity integer,
            room integer, grade string, phone string,
            mobileCarrier integer, paging text, parent1 text,
            parent2 text, parent1Link text, parent2Link text,
            parentEmail text, medical text, joinDate text,
            lastSeen text, lastModified text, count integer,
            visitor bool, expiry text, noParentTag bool,
            barcode integer, picture text, authorized integer,
            unauthorized integer, notes text);""")
        #barcode
        self.execute("""CREATE TABLE barcode(id integer primary key,
            value string, ref integer);""")
        #authorized
        self.execute("""CREATE TABLE authorized(id integer primary key,
            ref integer, name text, lastname text, dob text,
            docNumber text, photo text, document text, phoneHome text,
            phoneMobile text, mobileCarrier integer, notes string);""")
        #unauthorized
        self.execute("""CREATE TABLE unauthorized(id integer primary key,
            ref integer, name text, lastname text, photo text, document text,
            phone text, notes text);""")
        #volunteers
        self.execute("""CREATE TABLE volunteers(id integer primary key,
            name text, lastname text, dob text, email text,
            username text, phoneHome text, phoneMobile text,
            mobileCarrier integer, backgroundCheck bool,
            backgroundDocuments text, profession text, title text,
            company text, jobContact text, address text, city text,
            zip text, state text, country text, nametag bool,
            category text, subtitle text, services text, rooms text,
            notifoUser text, notifoSecret text,
            availability text, joinDate text, lastSeen text,
            lastModified text, picture text, notes text);""")
        #categories
        self.execute("""CREATE TABLE categories(id integer primary key,
            name text, admin integer);""")
        #users
        self.execute("""CREATE TABLE users(id integer primary key,
            user text UNIQUE NOT NULL, hash text, salt text, admin integer,
            notifoUser text, notifoSecret text, scATR text,
            leftHanded bool, ref integer, name text);""")
        #activities
        self.execute("""CREATE TABLE activities(id integer primary key,
            name text, prefix text, securityTag text, securityMode text,
            nametagEnable bool, nametag text,
            parentTagEnable bool, parentTag text,
            admin integer, autoExpire bool, notifyExpire integer,
            newsletter bool, newsletterLink text,
            registerSMSEnable bool, registerSMS text,
            registerEmailEnable bool, registerEmail text,
            checkinSMSEnable bool, checkinSMS text,
            checkinEmailEnable bool, checkinEmail text,
            parentURI text, alertText text);""")
        #services
        self.execute("""CREATE TABLE services(id integer primary key,
            name text, day integer, time text, endTime text);""")
        #rooms
        self.execute("""CREATE TABLE rooms(id integer primary key,
            name text NOT NULL, activity integer NOT NULL,
            volunteerMinimum integer, maximumOccupancy integer, camera text,
            cameraFPS integer, admin integer, notifoUser, notifoSecret,
            email text, mobile text, carrier integer);""")
        #carriers
        self.execute("""CREATE TABLE carriers(id integer primary key,
            name text, region text, address text, subject text,
            message text);""")
        #statistics
        self.execute("""CREATE TABLE statistics(id integer primary key,
            person integer, date text,
            service forgein key references services(id), expires text,
            checkin text, checkout text, code text, location text,
            volunteer integer, activity, room);""")
        self.log.info('Tables created')
        self.conn.commit()
        self.log.debug('Tables committed to database')
        return 0

    # == End __init__  ==


    # == data functions ==
    # Populate all fields for registering a child only. Entries without
    #   a default are mandatory.  Form should check for missing stuff.
    def Register(self, name, lastname, phone, parent1, paging='',
            mobileCarrier=0, activity=0, room=0, grade='', parent2='',
            parent1Link='', parent2Link='', parentEmail='', dob='',
            medical='', joinDate='', lastSeen='', lastModified='', count=0,
            visitor=False, expiry=None, noParentTag=None, barcode=None,
            picture='',  authorized=None, unauthorized=None, notes=''):
        """Enter a new child's record into the data table.

        name, lastname, phone, parent1, paging=''
        mobileCarrier=0, activity=0, room=0, grade='', parent2='',
        parent1Link='', parent2Link='', parentEmail='', dob=''
        medical='', joinDate='', lastSeen='', lastModified='', count=0
        visitor=False, noParentTag=False, barcode=None, picture='',
        authorized=None, unauthorized=None, notes=''

        Returns the id of the newly created record.

        Be sure to create entry in barcode, unauthorized, or authorized table
        before creating a record here.

        If registering, be sure to call this before checkin() on the record itself.
        Remember to call commit() after creating all these entries.
        """

        #set dates:
        if joinDate == '': #Generally should always be true (unless
            joinDate = str(datetime.date.today()) #importing from script

        if lastSeen == '':
            lastSeen = str(datetime.date.today())

        if lastModified == '':
            lastModified = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
            #~ lastModified = time.ctime() #should be plain ISO 8601 (close enough)

        #escape and execute
        self.execute("""INSERT INTO data(name, lastname, dob, phone,
        paging, parent1, mobileCarrier, activity, room, grade,
        parent2, parent1Link, parent2Link, parentEmail, medical,
        joinDate, lastSeen, lastModified, count, visitor, expiry,
        noParentTag, barcode, picture, notes) VALUES
        (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);""",
        (name, lastname, dob, phone, paging, parent1, mobileCarrier,
        activity, room, grade, parent2, parent1Link, parent2Link,
        parentEmail, medical, joinDate, lastSeen, lastModified, count,
        int(visitor), expiry, int(noParentTag), barcode, picture, notes))

        ret = self.execute("""SELECT id FROM data WHERE
                               name = ? AND lastname = ?
                               AND phone = ?""", (name, lastname, phone)).fetchall()
        if len(ret) > 1:
            for i in ret[0]:
                log.warn('Duplicate entry found at {0}.'.format(i[0]))
        if ret == []:
            raise DatabaseError(EMPTY_RESULT, 'Record not committed.')
        else:
            return ret[0][0]

    def Delete(self, index):
        """Delete a row in the data table by index."""
        self.execute("DELETE FROM data WHERE id = ?;", (index,))

    def Update(self, index, name, lastname, phone, parent1, paging='',
            mobileCarrier=0, activity=0, room=0, grade='', parent2='',
            parent1Link='', parent2Link='', parentEmail='', dob='',
            medical='', joinDate='', lastSeen='', count=0,
            visitor=False, expiry=None, noParentTag=None, barcode=None,
            picture='',  authorized=None, unauthorized=None, notes=''):
        """Update a record.  Pass index as first argument.  lastModified automatically set.

        index, name, lastname, dob, phone, paging, and parent1 are mandatory.
        Defaults are as follows: mobileCarrier=0, activity=0, room=0, grade='',
        parent2='', parent1Link='', parent2Link='', parentEmail='', medical='',
        joinDate='', lastSeen='', visitor=False,
        noParentTag=False, barcode='', picture='',  notes=''
        """
        self.execute("UPDATE data SET name=?, lastname=? WHERE id=?;", (name, lastname, index))
        self.execute("UPDATE data SET dob=? WHERE id=?;", (dob, index))
        self.execute("UPDATE data SET phone=?, paging=? WHERE id=?;",(phone, paging, index))
        self.execute("UPDATE data SET mobileCarrier=? WHERE id=?;",
            (mobileCarrier, index))
        self.execute("""UPDATE data SET parent1=?, parent2=?,
            parent1Link=?, parent2Link=? WHERE id=?""", (parent1,
            parent2, parent1Link, parent2Link, index))
        self.execute("UPDATE data SET activity=?, room=?, grade=? WHERE id=?;",
            (activity, room, grade, index))
        self.execute("UPDATE data SET parentEmail=?, medical=? WHERE id=?;",
            (parentEmail, medical, index))
        self.execute("UPDATE data SET joinDate=?, lastSeen=?, lastModified=? WHERE id=?;",
            (joinDate, lastSeen, time.ctime(), index))
        self.execute("""UPDATE data SET visitor=?, expiry=?, noParentTag=?,
            barcode=?,  picture=?, notes=? WHERE id=?;""", (int(visitor), expiry,
            int(noParentTag),  barcode, picture, notes, index))
    # === end data functions ===

    # === Check-in functions ===
    def DoCheckin(self, person, services, expires, code, location, activity, room, cursor=None):
        """
        person: id reference of who's being checked-in.
        services: a tuple of services to be checked-in for.  Pass singleton if only one.
            Services should be passed in chronological order!
        expires: expiration time, if applicable, of the last service chronologically.
        code: secure code, or hashed value on child's tag if not in simple mode.
        location: text location to identify kiosk used for check-in.
        activity: activity name as string.
        room: room name as string.
        """
        expiry = None
        for service in services:
            if services.index(service) + 1 == len(services): #On the last item
                expiry = expires
            #~ try:
            self.execute("""INSERT INTO statistics(person, date, service, expires,
                    checkin, checkout, code, location, activity, room)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""", (person,
                    str(datetime.date.today()), service, expiry,
                    time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
                    None, code, location, activity, room), cursor)
            #~ except sqlite.Error as e:
                #~ raise DatabaseError(UNKNOWN_ERROR, e.args[0])
                
        #~ #TODO: Incrament count, update last seen date.
        count = self.execute("SELECT count FROM data WHERE id = ?;", (person,)).fetchone()[0]
        self.log.debug("Updating record count: %s" % str(count))
        count = int(count) + 1
        today = datetime.date.today()
        self.execute("UPDATE data SET count = ?, lastSeen = ? WHERE id = ?;", 
            (count, today, person))

    def DoCheckout(self, person):
        """
        Marks a record as checked-out.
        """
        self.execute("UPDATE statistics SET checkout = ? WHERE person = ? AND date = DATE('now', 'localtime');",
            (time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()), person))
        self.commit()

    #return all entries (for browsing)
    def GetAll(self):
        """Returns all rows. (useful for browsing)"""
        return self.execute("SELECT * FROM data;").fetchall()

    def GetRecordByID(self, ref):
        """
        Returns a single row specified by id.
        """
        a = self.dict_factory(self.execute("SELECT * FROM data WHERE id = ?", (ref,)).fetchone())
        return a
    
    def GetActivityById(self, ref):
        """
        Returns dictionary of a given activity specified by id.
        """
        a = self.dict_factory(self.execute("SELECT * FROM activities WHERE id = ?;", (ref,)).fetchone())
        return a 
        

    def GetStatus(self, ref, full=False):
        """
        Returns the check-in status for a specified record, according to the
        constants defined in taxidi.py. (STATUS_NONE, STATUS_CHECKED_IN, or
        STATUS_CHECKED_OUT).  If full=True, then the status is returned as part
        of a dictionary of the matching statistics row.  Only returns values from
        today's date.
        """
        a = self.execute("SELECT * FROM statistics WHERE person = ? AND checkin > date('now', 'localtime');", (ref,))
        ret = []
        for i in a.fetchall():
            ret.append(self.dict_factory(i)) #return as a nested dictionary

        if len(ret) == 0:
            if full:
                return { 'status': taxidi.STATUS_NONE, 'code': None }
            return taxidi.STATUS_NONE
        elif len(ret) == 1:
            #Only one check-in. Return what's appropriate:
            ret = ret[0]
        else:
            #Just check the last check-in for now
            ret = ret[-1]

        if ret['checkin'] == None:  #Not checked-in (this shouldn't happen)
            if full:
                ret['status'] = taxidi.STATUS_NONE
                return ret
            return taxidi.STATUS_NONE
        else:
            if ret['checkout'] == None: #Checked-in
                if full:
                    ret['status'] = taxidi.STATUS_CHECKED_IN
                    return ret
                return taxidi.STATUS_CHECKED_IN
            else:
                if full:
                    ret['status'] = taxidi.STATUS_CHECKED_OUT
                    return ret
                return taxidi.STATUS_CHECKED_OUT
        
    """
    Returns list of all children checked in to the system, suitable for 
    printing a report.
    """
    def GetEmergencyList(self):
        #TODO: Filter by activity/room
        a = self.execute("""SELECT data.*, statistics.* FROM data 
        INNER JOIN statistics ON data.id = statistics.person 
        WHERE statistics.date = DATE('now', 'localtime');""")
        ret = []
        for i in a.fetchall():
            ret.append(self.dict_factory(i)) #return as a nested dictionary
        return ret

    # === begin search functions ===
    def Search(self, query):
        """
        Generic search function.

        Searches first through `data`, then passes to SearchVolunteer()
        Accepts query as first argument.  Searches the following in data table:
        - Last four digits of phone number (if len == 4)
        - paging(?)
        - lastname
        - firstname
        Then searches through volunteers table.
        """
        a = []

        if query.isdigit() and (len(query) == 4 or len(query) == 7) \
          or query[0] == '+':
            #search by phone.
            a = self.SearchPhone(query)
        if not query.isdigit():  #Search in names.
            a = self.SearchName(query)
            if len(a) == 0:
                #Search partial names:
                a = self.SearchName(query+'%')
        if len(query) == 3:
            a = self.SearchSecure(query)
        if len(a) == 0: #Catch barcodes
            a = self.SearchBarcode(query)

        #TODO: Search volunteers:
        return a


    def SearchName(self, query):
        """
        Searches only in name, lastname, parent's column.
        Returns *.  '*' and '%' are treated as wild-card characters, and will
        search using the LIKE operator.
        """
        if ("%" in query) or ("*" in query):
            query = query.replace("*", "%")

            a = self.execute("""SELECT DISTINCT {0} FROM data WHERE name LIKE ?
                                OR lastname LIKE ?
                                or parent1 LIKE ?
                                or parent2 LIKE ?
                                ORDER BY lastname;
                                """.format(self.columns), (query,)*4)
        else:
            a = self.execute("""SELECT DISTINCT {0} FROM data WHERE
                                name = ? COLLATE NOCASE
                                OR lastname = ? COLLATE NOCASE
                                OR parent1 = ? COLLATE NOCASE
                                OR parent2 = ? COLLATE NOCASE
                                ORDER BY lastname;
                                """.format(self.columns), (query,)*4)
        ret = []
        for i in a.fetchall():
            ret.append(self.dict_factory(i)) #return as a nested dictionary
        return ret

    def SearchBarcode(self, query):
        """
        Searches for an entry (only in the data table) by barcode.
        """
        a = self.execute("""SELECT DISTINCT {0} FROM data
                            INNER JOIN barcode ON data.id = barcode.ref
                            WHERE barcode.value = ?
                            """.format(self.columns), (query,))
        ret = []
        for i in a.fetchall():
            ret.append(self.dict_factory(i)) #return as a nested dictionary
        return ret

    def SearchPhone(self, query):
        """
        Searches for an entry by entire or last four digits of phone number.
        """
        query = str(query)
        #Most of this is taken out of my input validator
        if len(query) == 4:
            #Search by last four:
            query = '%' + query
            a = self.execute("""SELECT DISTINCT {0} FROM data
                                WHERE phone LIKE ?
                                ORDER BY lastname;
                                """.format(self.columns), (query,))

        elif query.isdigit() and len(query) == 10 \
          and query[0] not in '01' and query[3] not in '01':  #US: '4805551212'
            a = self.execute("""SELECT DISTINCT {0} FROM data
                                WHERE phone = ?
                                ORDER BY lastname;
                                """.format(self.columns), (query,))

        elif len(query) == 12 and query[3] in '.-/' \
          and query[7] in '.-/':  #US: '334-555-1212'
            trans = Translator(delete='+(-)./ ')
            query = trans(query.encode('ascii'))
            a = self.execute("""SELECT DISTINCT {0} FROM data
                                WHERE phone = ?
                                ORDER BY lastname;
                                """.format(self.columns), (query,))

        elif query[0] == '(' and len(query) == 14: #US: (480) 555-1212
            query = query[1:4] + query[6:9] + query[10:14]
            a = self.execute("""SELECT DISTINCT {0} FROM data
                                WHERE phone = ?
                                ORDER BY lastname;
                                """.format(self.columns), (query,))

        elif query[0] == '+':  #International format
            trans = Translator(delete='+(-)./ ')
            query = trans(query.encode('ascii'))
            a = self.execute("""SELECT DISTINCT {0} FROM data
                                WHERE phone = ?
                                ORDER BY lastname;
                                """.format(self.columns), (query,))

        elif len(query) == 7:
            #Search by last seven:
            query = '%' + query
            a = self.execute("""SELECT DISTINCT {0} FROM data
                                WHERE phone LIKE ?
                                ORDER BY lastname;
                                """.format(self.columns), (query,))

        else:
            self.log.warn("Search key {0} probably isn't a phone number.")
            a = self.execute("""SELECT DISTINCT {0} FROM data
                                WHERE phone = ?
                                ORDER BY lastname;
                                """.format(self.columns), (query,))

        ret = []
        for i in a.fetchall():
            ret.append(self.dict_factory(i)) #return as a nested dictionary
        return ret

    def SearchSecure(self, query):
        """
        Searches for a record by the security code assigned at check-in, if applicable.
        """
        a = self.execute("""SELECT DISTINCT {0} FROM data
                            INNER JOIN statistics ON data.id = statistics.person
                            WHERE statistics.code = ?;
                            """.format(self.columns), (query,))
        ret = []
        for i in a.fetchall():
            ret.append(self.dict_factory(i)) #return as a nested dictionary
        return ret
    # === end search functions ===

    # === barcode functions ===
    def GetBarcodes(self, record):
        """
        Returns all barcodes listed for a given record ID.
        """
        a = self.execute("""SELECT DISTINCT id, value FROM barcode
                            WHERE ref = ? ORDER BY id""", (record,))
        return self.to_dict(a)

    def AddBarcode(self, record, value):
        self.execute("""INSERT INTO barcode(value, ref)
                        VALUES (?, ?)""", (value, record))

    def RemoveBarcode(self, ref):
        self.execute("DELETE FROM barcode WHERE id = ?;", (ref,))

    def RemoveAllBarcodes(self, ref):
        """
        Deletes all barcodes for a given record (nuke)
        """
        self.execute("DELETE FROM barcode WHERE ref = ?;", (ref,))

    def UpdateBarcode(self, ref, value):
        self.execute("UPDATE barcode SET value = ? WHERE id = ?", (value, ref))
    # === end barcode functions ===

    # === services functions ===
    def GetServices(self):
        return self.to_dict(self.execute("SELECT * FROM services;"))

    def AddService(self, name, day=0, time='00:00:00', endTime='23:59:59'):
        self.execute("""INSERT INTO services(name, day, time, endTime)
                        VALUES (?, ?, ?, ?);""", (name, day, time, endTime))

    def RemoveService(self, ref):
        self.execute("DELETE FROM services WHERE id = ?;", (ref,))

    def UpdateService(self, ref, name, day, time, endTime):
        self.execute("""UPDATE services SET name = ?,
                        day = ?, time = ?, endTime = ? WHERE id = ?;""",
                        (name, day, time, endTime, ref))
    # === end services functions ===

    # === activities functions ===
    def GetActivities(self):
        return self.to_dict(self.execute("SELECT * FROM activities;"))

    def GetActivity(self, ref):
        """
        Converts a reference to the activity table to an explicit string value
        (for reading a record's assigned activity with no forgein key support).
        """
        return self.execute("SELECT name FROM activities WHERE id = ?;", (ref,)).fetchone()[0]

    def AddActivity(self, name, prefix='', securityTag=False, securityMode='simple',
                    nametag='default', nametagEnable=True,
                    parentTag='default', parentTagEnable=True, admin=None,
                    autoExpire = False, notifyExpire = False, newsletter=False,
                    newsletterLink='', alert=''):
        if prefix == '' or prefix == None:
            prefix = name[0].upper()
        self.execute("""INSERT INTO activities(name, prefix, securityTag,
                        securityMode, nametagEnable, nametag,
                        parentTagEnable, parentTag, admin, autoExpire,
                        notifyExpire, newsletter, newsletterLink, alertText)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                        (name, prefix, securityTag, securityMode,
                        nametagEnable, nametag, parentTagEnable, parentTag,
                        admin, autoExpire, notifyExpire, newsletter,
                        newsletterLink, alert))

    def RemoveActivity(self, ref):
        self.execute("DELETE FROM activities WHERE id = ?;", (ref,))
        pass

    def UpdateActivity(self, ref, name, prefix, securityTag, securityMode,
                       nametag, nametagEnable, parentTag,
                       parentTagEnable, admin, autoExpire, notifyExpire,
                       newsletter, newsletterLink):
        if prefix == '' or prefix == None:
            prefix = name[0].upper()
        self.execute("""UPDATE activities SET name = ?, prefix = ?,
                        securityTag = ?, securityMode = ?,
                        nametag = ?, nametagEnable = ?, parentTag = ?,
                        parentTagEnable = ?, admin = ?, autoExpire = ?,
                        notifyExpire = ?, newsletter = ?,
                        newsletterLink = ? WHERE id = ?;""", (name, prefix,
                        securityTag, securityMode, nametag,
                        nametagEnable, parentTag, parentTagEnable, admin,
                        autoExpire, notifyExpire, newsletter,
                        newsletterLink, ref))
    # === end activities functions ==

    # === rooms functions ===
    def AddRoom(self, name, activity, volunteerMinimum=0, maximumOccupancy=0,
                camera='', cameraFPS=0, admin=0, notifoUser=None,
                notifoSecret=None, email='', mobile='', carrier=None):
        #Check to see that activity exists:
        ret = self.execute('SELECT id FROM activities WHERE id = ?;',
            (activity,)).fetchall()
        if len(ret) == 1:
            #Activity exists.  Create room.
            self.execute("""INSERT INTO rooms(name, activity, volunteerMinimum,
                            maximumOccupancy, camera, cameraFPS, admin,
                            notifoUser, notifoSecret, email, mobile, carrier)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (name, activity, volunteerMinimum, maximumOccupancy,
                            camera, cameraFPS, admin, notifoUser,
                            notifoSecret, email, mobile, carrier))
            return SUCCESS
        else:
            return CONSTRAINT_FAILED #Forgein key constraint failed

    def GetRooms(self):
        return self.to_dict(self.execute('SELECT * FROM rooms;'))

    def GetRoomByID(self, ref):
        """
        Returns a room name specified from a reference (for displaying results).
        """
        a = self.execute('SELECT name FROM rooms WHERE id = ?;', (ref,)).fetchone()
        if a != None:
            return a[0]
        else:
            return ''

    def GetRoom(self, activity):
        """
        Returns rooms dictionary matching a given activity (by name).
        """
        return self.to_dict(self.execute("""SELECT rooms.*
                                            FROM rooms
                                            INNER JOIN activities ON
                                            activities.id = rooms.activity
                                            WHERE activities.name = ?;""",
                                            (activity,)))

    def GetRoomID(self, name):
        """
        Return's a room's primary key (id) given a name.
        """
        return self.execute("SELECT id FROM rooms WHERE name = ?;", (name,)).fetchone()

    def RemoveRoom(self, ref):
        self.execute("DELETE FROM rooms WHERE id = ?;", (ref,))

    # === users functions ===
    def GetUsers(self):
        a = self.execute("""SELECT user, admin, notifoUser, notifoSecret,
                            scATR, leftHanded, ref FROM users;""")
        return self.to_dict(a)

    def GetUser(self, user):
        #Should only return one row
        return self.to_dict(self.execute("SELECT * FROM users WHERE user = ?;", (user,)))[0]

    def UserExists(self, user):
        a = self.execute("SELECT id FROM users WHERE user = ?;", (user,)).fetchall()
        if len(a) == 0:
            return False
        else:
            return True

    def AddUser(self, user, password, admin=False, notifoUser=None,
                notifoSecret=None, scATR=None, leftHanded=False, ref=None):
        #Check that the user doesn't exist:
        if len(self.execute("SELECT * FROM users WHERE user = ?;", \
          (user,)).fetchall()) != 0:
            return USER_EXISTS

        salt = os.urandom(29).encode('base_64').strip('\n') #Get a salt
        if password == '': #Set a random password
            password = os.urandom(8).encode('base_64').strip('\n')
        ph = hashlib.sha256(password + salt)
        ph.hexdigest()

        try:
            self.execute("""INSERT INTO users(user, hash, salt, admin, notifoUser,
                            notifoSecret, scATR, leftHanded, ref) VALUES
                            (?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                            (user, ph.hexdigest(), salt, admin, notifoUser,
                            notifoSecret, scATR, leftHanded, ref))
        except sqlite.IntegrityError:
            return USER_EXISTS
        return SUCCESS

    def RemoveUser(self, user):
        """
        Remove an user from the system by username.
        """
        self.execute("DELETE FROM users WHERE user = ?;", (user,))

    def AuthenticateUser(self, user, password):
        if self.UserExists(user):
            info = self.GetUser(user)
            passhash = hashlib.sha256(password + info['salt'])
            if info['hash'] == passhash.hexdigest():
                return 1
        return 0
    # == end users functions ==


    # Add a volunteer
    def RegisterVolunteer(self, name, lastname, dob, phoneHome, email='',
            username='', phoneMobile='', mobileCarrier=0,
            backgroundCheck=False, backgroundDocuments='',
            profession='', title='', company='', jobContact='',
            address='', city='', zipcode='', state='', country='',
            nametag=False, category='', subtitle='', services='',
            rooms='', availability='', joinDate='', lastSeen='',
            lastModified='', picture='', notes=''):
        """Register a volunteer.

        name, lastname, dob, and phoneHome are mandatory.
        Defaults are as follows:  email='', username='', phoneMobile='',
        mobileCarrier=0, backgroundCheck=False, backgroundDocuments='',
        profession='', title='', company='', jobContact='',  address='',
        city='', zipcode='', state='', country='', nametag=False,
        category='', subtitle='', services='', rooms='', availability='',
        joinDate='', lastSeen='',  lastModified='', picture='', notes=''
        """

        #set dates:
        if joinDate == '': #Generally should always be true (unless
            joinDate = datetime.date.today() #importing from script

        if lastSeen == '':
            joinDate = datetime.date.today()

        if lastModified == '': #Use ISO 8601, not ctime()
            lastModified == time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
            #~ lastModified == time.ctime() 

        #execute
        self.execute("""INSERT INTO volunteers(name, lastname, dob,
            phoneHome, email, username, phoneMobile, mobileCarrier,
            backgroundCheck, backgroundDocuments, profession, title,
            company, jobContact, address, city, zipcode, state, country,
            nametag, category, subtitle, services, rooms, availability,
            joinDate, lastSeen, lastModified, picture, notes) VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);""",
            name, lastname, dob, phoneHome, email, username, phoneMobile,
            mobileCarrier, int(backgroundCheck), backgroundDocuments,
            profession, title, company, jobContact, address, city,
            zipcode, state, country, int(nametag), category, subtitle,
            services, rooms, availability, joinDate, lastSeen,
            lastModified, picture, notes)


    # == category functions ==
    def GetCategories(self):
        """Returns all categories"""
        return to_dict(self.execute("SELECT * FROM categories;"))

    def AddCategory(self, name, admin=0):
        """Add a category (ministry): Parking, café, etc."""
        self.execute("INSERT INTO categories(name, admin) VALUES (?,?);",
            (name, admin))

    def DeleteCategory(self, index):
        """Delete a category by index. Pass 0 to delete all."""
        if index == 0:
            self.log.warning("Deleting all rows in table 'categories'")
            self.execute("DELETE FROM categories;") #deletes all rows
        else:
            self.execute("DELETE FROM categories WHERE id = ?;", [index])

    def UpdateCategory(self, index, name, admin='0'):
        """Update name or admin status in categories table"""
        self.execute("UPDATE categories SET name = ?, admin = ? WHERE id = ?;",
            (name, admin, index))

    # == end categories ==


    # == generic SQL functions ==
    def execute(self, sql, args=(''), cursor=None):
        """Executes SQL, reporting debug to the log. For internal use."""
        if cursor == None: cursor = self.cursor
        if self.debug:
            sql = sql.replace('    ', '').replace('\n', ' ')  #make it pretty
            self.log.debug((str(cursor).split()[-1][:-1], sql, args))
        try:
            data = cursor.execute(sql, args)
            return data
        except sqlite.OperationalError as e:
            self.log.error('SQLite3 returned operational error: {0}'
                .format(e))
            if self.conn:
                self.conn.rollback()    #drop any changes to preserve db.
            raise

    #To keep things speedy we need to be able to commit from the calling module
    def commit(self):
        """Commit SQL to the database. Use sparingly for best performance."""
        self.log.debug('Committed database')
        return self.conn.commit()   # Should be used sparingly otherwise

    def dict_factory(self, row):
        d = {}
        for idx, col in enumerate(self.cursor.description):
            d[col[0]] = row[idx]
        return d

    def to_dict(self, inp):
        """
        Converts results from an sql.execute() to a nested dictionary.
        """
        ret = []
        for i in inp.fetchall():
            ret.append(self.dict_factory(i)) #return as a nested dictionary
        return ret

    # == end generic functions ==

class DatabaseError(Exception):
    def __init__(self, code, value=''):
        if value == '':
            self.error = 'Generic database error.'
            if code == EMPTY_RESULT:
                self.error = 'Query returned empty result'
            elif code == CONSTRAINT_FAILED:
                self.error = 'Unique key constraint failed.'
            elif code == USER_EXISTS:
                self.error = 'The user specified already exists.'
        else:
            self.error = value
        self.code = code
    def __str__(self):
        return repr(self.error)

def Translator(frm='', to='', delete='', keep=None):
    """
    Wrapper around string.translate().
    Note that translate() does not support unicode objects.

    """
    allchars = string.maketrans('','')
    if len(to) == 1:
        to = to * len(frm)
    trans = string.maketrans(frm, to)
    if keep is not None:
        delete = allchars.translate(allchars, keep.translate(allchars, delete))
    def callable(s):
        return s.translate(trans, delete)
    return callable


if __name__ == '__main__':
    try:
        db = Database('~/.taxidi/database/users.db')
        #~ db = Database('~/test.db')
        if db.status == NEW:
            #Show a nice welcome dialogue, etc.
            pass
    except TypeError:
        print 'Unable to open database (file write-protected?)'
        #display an error dialogue and exit

    #Searching
    #~ print db.SearchName('Gal*')
    #~ print db.SearchBarcode('1234')
    #~ print db.SearchPhone('1212')
    #~ print db.Search('wolf') #Full system search (default)

    #Barcodes
    #~ print db.GetBarcodes(300)
    #~ db.AddBarcode(300, 'taxidi')
    #~ db.commit()
    #~ print db.SearchBarcode('taxidi')
    #~ print
    #~ barcodes = db.GetBarcodes(300)
    #~ db.UpdateBarcode(barcodes[0]['id'], 'Tax=id=i')
    #~ print db.SearchBarcode('Tax=id=i')
    #~ if len(barcodes) > 0:
        #~ db.RemoveBarcode(barcodes[0]['id'])
    #~ db.commit()

    #Services
    #~ db.AddActivity('Outfitters')
    #~ activities = db.GetActivities()
    #~ db.UpdateActivity(activities[0]['id'], 'Route 56', None, False, 'none', 'default', 'default', True, 'default', False, None, True, None)
    #~ db.commit()
    #~ db.RemoveActivity(1)
    #~ print db.GetActivities()

    #Users
    #~ if db.AddUser('guest', 'password', admin=False) == USER_EXISTS: print "User admin already exists"
    #~ db.commit()
    #~ print db.GetUsers()
    #~ print
    #~ print (db.AuthenticateUser('admin', 'badpassword') == AUTHORIZED) #False
    #~ print (db.AuthenticateUser('baduser', 'pass') == AUTHORIZED)      #False
    #~ print (db.AuthenticateUser(u'admin', u'password') == AUTHORIZED)    #True
    #~ db.RemoveUser('admin') ; db.commit()
    #~ print (db.AuthenticateUser('admin', 'password') == AUTHORIZED)    #False

    #~ db.AddService('Second Service')
    #~ db.UpdateService(1, 'First Service', 7, '09:00:00', '09:59:00')
    #~ db.commit()
    #~ print db.GetServices()

    #Activities:
    #~ db.AddActivity('Explorers', parentTagEnable=True, newsletter=True)
    #~ db.AddActivity('Outfitters', parentTagEnable=False, newsletter=False)
    #~ print db.GetActivities()
    import pprint
    pprint.pprint(db.GetEmergencyList())

    #Rooms
    #~ print bool(db.AddRoom('Outfitters Room', 2) & SUCCESS)
    #~ print db.GetRooms()
    #~ print
    #~ print db.GetRoom('Explorers')
    #~ db.RemoveRoom(3)

    #Check-in:
    #~ db.DoCheckin(632, ('First Service', 'Second Service', 'Third Service'), '14:59:59', '5C55', 'Kiosk1', 'Explorers', 'Jungle Room')

    #~ print db.GetServices()
    #~ print db.GetStatus(799, True)
    #~ print db.SearchSecure("C0W")[0]['id']
    
    #~ print db.GetActivities()
    db.commit()

    db.close()
