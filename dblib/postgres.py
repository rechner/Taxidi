#!/usr/bin/env python
#-*- coding:utf-8 -*-

# dblib/postgres.py (spaces, not tabs)
# PostgreSQL database driver for Taxídí.
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

#Don't forget to commit the database often, even after a select.
#Had problems with the 'data' table being a reserved keyword, so table
# and column names should always be escaped.  Column names are case-
# insensitive otherwise.

debug = True

import os
import sys
import logging
import time
import datetime
import psycopg2
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
INVALID_PASSWORD = 64
AUTHORIZED = 1
UNAUTHORIZED = 0
NEW = 128
RESET_TABLES = 256

#Database schema version (integer):
database_version = 1

class Database:
    """
    PostgreSQL driver for Taxídí database.
    """
    def __init__(self, host, dbname, user, password, location='pyTaxidi'):
        """
        Opens connection to a PostgreSQL database.  Creates tables if they don't
        exist, but expects the database was created by the admin.
        """

        self.columns = """data.id, name, lastname, dob, data.activity, data.room, grade, phone,
                          "mobileCarrier", paging, parent1, "parent1Link", parent2,
                          "parent2Link", "parentEmail", medical, "joinDate", "lastSeen",
                          "lastModified", count, visitor, "noParentTag", barcode,
                          picture, authorized, unauthorized, notes"""
                          
        self.tables = [ "data", 'barcode', 'authorized', 'unauthorized',
                       'volunteers', 'categories', 'users', 'activities',
                       'services', 'rooms', 'carriers', 'statistics' ]
        self.tableSQL = []
        self.tableSQL.append("""CREATE TABLE data(id SERIAL primary key,
            name text, lastname text,  dob text, activity integer,
            room integer, grade text, phone text,
            "mobileCarrier" integer, paging text, parent1 text,
            parent2 text, "parent1Link" text, "parent2Link" text,
            "parentEmail" text, medical text, "joinDate" DATE,
            "lastSeen" DATE, "lastModified" TIMESTAMP, count integer,
            visitor bool, expiry text, "noParentTag" bool,
            barcode integer, picture text, authorized integer,
            unauthorized integer, notes text);""")
        self.tableSQL.append("""CREATE TABLE barcode(id SERIAL primary key ,
            value text NOT NULL, ref integer REFERENCES "data"(id));""")
        self.tableSQL.append("""CREATE TABLE authorized(id SERIAL,
            ref integer, name text, lastname text, dob text,
            "docNumber" text, photo text, document text, "phoneHome" text,
            "phoneMobile" text, "mobileCarrier" integer, notes text);""")
        self.tableSQL.append("""CREATE TABLE unauthorized(id SERIAL,
            ref integer, name text, lastname text, photo text, 
            document text, phone text, notes text);""")
        self.tableSQL.append("""CREATE TABLE volunteers(id SERIAL,
            name text, lastname text, dob text, email text,
            username text, "phoneHome" text, "phoneMobile" text,
            "mobileCarrier" integer, "backgroundCheck" bool,
            "backgroundDocuments" text, profession text, title text,
            company text, "jobContact" text, address text, city text,
            zip text, state text, country text, nametag bool,
            category text, subtitle text, services text, rooms text,
            "notifoUser" text, "notifoSecret" text,
            availability text, "joinDate" DATE, "lastSeen" DATE,
            "lastModified" TIMESTAMP, picture text, notes text);""")
        self.tableSQL.append("""CREATE TABLE categories(id SERIAL,
            name text, admin integer);""")
        self.tableSQL.append("""CREATE TABLE users(id SERIAL,
            "user" text UNIQUE NOT NULL, hash text, salt text, 
            admin bool, "notifoUser" text, "notifoSecret" text, 
            "scATR" text, "leftHanded" bool, ref int, name text);""")
        self.tableSQL.append("""CREATE TABLE activities(id SERIAL,
            name text, prefix text, "securityTag" text, "securityMode" text,
            "nametagEnable" bool, nametag text,
            "parentTagEnable" bool, "parentTag" text,
            admin integer, "autoExpire" bool, "notifyExpire" bool,
            newsletter bool, "newsletterLink" text,
            "registerSMSEnable" bool, "registerSMS" text,
            "registerEmailEnable" bool, "registerEmail" text,
            "checkinSMSEnable" bool, "checkinSMS" text,
            "checkinEmailEnable" bool, "checkinEmail" text,
            "parentURI" text, "alertText" text);""")
        self.tableSQL.append("""CREATE TABLE services(id SERIAL,
            name text, day integer, time TIME, "endTime" TIME);""")
        self.tableSQL.append("""CREATE TABLE rooms(id SERIAL,
            name text NOT NULL, activity integer NOT NULL,
            "volunteerMinimum" integer, "maximumOccupancy" integer, camera text,
            "cameraFPS" integer, admin integer, "notifoUser" text, "notifoSecret" text,
            email text, mobile text, carrier integer);""")
        self.tableSQL.append( """CREATE TABLE carriers(id SERIAL,
            name text, region text, address text, subject text,
            message text);""")
        self.tableSQL.append("""CREATE TABLE statistics(id SERIAL,
            person integer, date date,
            service text, expires text,
            checkin timestamp, checkout timestamp, code text, location text,
            volunteer integer, activity text, room text);""")


        #Setup logging
        self.log = logging.getLogger(__name__)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(asctime)s] %(module)-6s  [%(levelname)-8s]  %(message)s')
        ch.setFormatter(formatter)
        self.log.addHandler(ch)
        if debug:
            self.log.setLevel(logging.DEBUG)
        else:
            self.log.setLevel(logging.INFO)

        #Create connection:
        try: #TODO: Add SSL/SSH tunnel
            if ':' in host:
                host, port = host.split(':')
            else:
                port = 5432
            self.conn = psycopg2.connect(host=host, database=dbname, 
                user=user, password=password, port=port)
                #application_name=location)
                                                                                        
            self.cursor = self.conn.cursor()
        except psycopg2.OperationalError as e:
            if e.pgcode == '28P01' or e.pgcode == '28000':
                raise DatabaseError(INVALID_PASSWORD)
            else:
                #Unhandled error.  Show it to the user.
                raise DatabaseError(FAIL, e)

        self.log.info("Created PostgreSQL database instance on host {0}.".format(host))
        self.log.debug("Checking for tables and creating them if not present....")
        self.status = OK
        self.createTables()
        
    def spawnCursor(self):
        """
        Returns a new cursor object (for multi-threadding use).
        Delete it when done.
        """
        return self.conn.cursor()
        
    def createTables(self):
        for i in range(len(self.tables)):
            
            #Not user-controled data, so a .format() is okay here.
            exists = self.execute(
              "SELECT true FROM pg_class WHERE relname = '{0}';".format(self.tables[i]))            
            
            if not exists:
                #Create it:
                self.status = RESET_TABLES
                self.log.info("Creating table {0}".format(self.tables[i]))
                self.execute(self.tableSQL[i])
                self.commit()
        self.commit()

    def commit(self):
        self.log.debug('Committed database')
        self.conn.commit()

    def close(self):
        """
        Close the connection and clean up the objects.
        Don't forget to call this when exiting the program.
        """
        self.cursor.close()
        self.conn.close()
        del self.cursor
        del self.conn
        
    def execute(self, sql, args=(''), cursor=None):
        """Executes SQL, reporting debug to the log. For internal use."""
        if debug:
            sql = sql.replace('    ', '').replace('\n', ' ')  #make it pretty
            if args != (''):
                self.log.debug(sql % args)
            else:
                self.log.debug(sql)
        try:
            self.cursor.execute(sql, args)
            try:
                return self.cursor.fetchall()
            except psycopg2.ProgrammingError:
                return True
        except (psycopg2.ProgrammingError, psycopg2.OperationalError) as e:
            self.log.error('psycopg2 returned operational error: {0}'
                .format(e))
            if self.conn:
                self.conn.rollback()    #drop any changes to preserve db.
            raise
            
    def dict_factory(self, row):
        d = {}
        for idx, col in enumerate(self.cursor.description):
            d[col[0]] = row[idx]
        return d

    def to_dict(self, a):
        """
        Converts results from a cursor object to a nested dictionary.
        """
        ret = []
        for i in a:
            ret.append(self.dict_factory(i)) #return as a nested dictionary
        return ret
        
    # == data functions ==
    # Populate all fields for registering a child only. Entries without
    #   a default are mandatory.  Form should check for missing stuff.
    def Register(self, name, lastname, phone, parent1, paging='',
            mobileCarrier=0, activity=0, room=0, grade='', parent2='',
            parent1Link='', parent2Link='', parentEmail='', dob='',
            medical='', joinDate='', lastSeen='', lastModified='', count=0,
            visitor=False, expiry=None, noParentTag=None, barcode=None,
            picture='',  authorized=None, unauthorized=None, notes=''):
        """Enter a new child's record into the `"data"` table.

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
            lastSeen = str(datetime.date.today()) #ISO8601 (YYYY-MM-DD)

        if lastModified == '':
            #should be plain ISO 8601 (required for Postgres timestamp type)
            #~ lastModified = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
            lastModified = datetime.datetime.now()
            #~ lastModified = time.ctime() #without timezone.

        #escape and execute
        self.execute("""INSERT INTO "data"(name, lastname, dob, phone,
        paging, parent1, "mobileCarrier", activity, room, grade,
        parent2, "parent1Link", "parent2Link", "parentEmail", medical,
        "joinDate", "lastSeen", "lastModified", count, visitor, expiry,
        "noParentTag", barcode, picture, notes) VALUES
        (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);""",
        (name, lastname, dob, phone, paging, parent1, mobileCarrier,
        activity, room, grade, parent2, parent1Link, parent2Link,
        parentEmail, medical, joinDate, lastSeen, lastModified, count,
        visitor, expiry, noParentTag, barcode, picture, notes))
        self.commit()

        ret = self.execute("""SELECT id FROM "data" WHERE
                               name = %s AND lastname = %s
                               AND phone = %s""", (name, lastname, phone))
        self.commit()
        
        if len(ret) > 1:
            for i in ret[0]:
                self.log.warn('Duplicate entry found at {0}.'.format(i))
        if ret == []:
            raise DatabaseError(EMPTY_RESULT, 'Record not committed.')
        else:
            return ret[0][0]
            
    def Delete(self, index):
        """Delete a row in the data table by index."""
        self.execute("DELETE FROM \"data\" WHERE id = %s;", (index,))
        self.commit()
        
    def Update(self, index, name, lastname, phone, parent1, paging='',
            mobileCarrier=0, activity=0, room=0, grade='', parent2='',
            parent1Link='', parent2Link='', parentEmail='', dob='',
            medical='', joinDate=None, lastSeen=None, count=0,
            visitor=False, expiry=None, noParentTag=None, barcode=None,
            picture='',  authorized=None, unauthorized=None, notes=''):
        """Update a record.  Pass index as first argument.  lastModified automatically set.

        index, name, lastname, dob, phone, paging, and parent1 are mandatory.
        Defaults are as follows: mobileCarrier=0, activity=0, room=0, grade='',
        parent2='', parent1Link='', parent2Link='', parentEmail='', medical='',
        joinDate='', lastSeen='', visitor=False,
        noParentTag=False, barcode='', picture='',  notes=''
        """
        try:
            self.execute("UPDATE \"data\" SET name=%s, lastname=%s WHERE id=%s;", (name, lastname, index))
            self.execute("UPDATE \"data\" SET dob=%s WHERE id=%s;", (dob, index))
            self.execute("UPDATE \"data\" SET phone=%s, paging=%s WHERE id=%s;",(phone, paging, index))
            self.execute("UPDATE \"data\" SET \"mobileCarrier\"=%s WHERE id=%s;",
                (mobileCarrier, index))
            self.execute("""UPDATE "data" SET parent1=%s, parent2=%s,
                "parent1Link"=%s, "parent2Link"=%s WHERE id=%s""", (parent1,
                parent2, parent1Link, parent2Link, index))
            self.execute("UPDATE \"data\" SET activity=%s, room=%s, grade=%s WHERE id=%s;",
                (activity, room, grade, index))
            self.execute("UPDATE \"data\" SET \"parentEmail\"=%s, medical=%s WHERE id=%s;",
                (parentEmail, medical, index))
            if joinDate != None:
                self.execute("UPDATE \"data\" SET \"joinDate\"=%s WHERE id=%s;",
                    (joinDate, index))
            if lastSeen != None:
                self.execute("UPDATE \"data\" SET \"lastSeen\"=%s WHERE id=%s;",
                    (lastSeen, index))
            self.execute("UPDATE \"data\" SET \"lastModified\"=%s WHERE id=%s;",
                (datetime.datetime.now(), index))
            self.execute("""UPDATE "data" SET visitor=%s, expiry=%s, "noParentTag"=%s,
                barcode=%s,  picture=%s, notes=%s WHERE id=%s;""", (visitor, expiry,
                noParentTag,  barcode, picture, notes, index))
        except psycopg2.Error as e:
            self.log.error(e)
            self.log.error("Error while updating. Rolling back transaction....")
            self.conn.rollback()
            raise
        self.commit()
    # === end data functions ===
    
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
        #check if hex:
        try:
            hexval = int(query, 16)
            isHex = True
        except:
            isHex = False
            
        if len(query) == 3 or (isHex and len(query) == 4) and len(a) == 0:
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

            a = self.execute("""SELECT DISTINCT {0} FROM "data" WHERE name LIKE %s
                                OR lastname LIKE %s
                                or parent1 LIKE %s
                                or parent2 LIKE %s
                                ORDER BY lastname;
                                """.format(self.columns), (query,)*4)
        else:
            a = self.execute("""SELECT DISTINCT {0} FROM "data" WHERE
                                name ILIKE %s
                                OR lastname ILIKE %s 
                                OR parent1 ILIKE %s
                                OR parent2 ILIKE %s
                                ORDER BY lastname;
                                """.format(self.columns), (query,)*4)
        ret = []
        for i in a:
            ret.append(self.dict_factory(i)) #return as a nested dictionary
        return ret

    def SearchBarcode(self, query):
        """
        Searches for an entry (only in the data table) by barcode.
        """
        a = self.execute("""SELECT DISTINCT {0} FROM "data"
                            INNER JOIN barcode ON "data".id = barcode.ref
                            WHERE barcode.value = %s;
                            """.format(self.columns), (query,))
        ret = []
        for i in a:
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
            a = self.execute("""SELECT DISTINCT {0} FROM "data"
                                WHERE phone LIKE %s
                                ORDER BY lastname;
                                """.format(self.columns), (query,))

        elif query.isdigit() and len(query) == 10 \
          and query[0] not in '01' and query[3] not in '01':  #US: '4805551212'
            a = self.execute("""SELECT DISTINCT {0} FROM "data"
                                WHERE phone = %s
                                ORDER BY lastname;
                                """.format(self.columns), (query,))

        elif len(query) == 12 and query[3] in '.-/' \
          and query[7] in '.-/':  #US: '334-555-1212'
            trans = Translator(delete='+(-)./ ')
            query = trans(query.encode('ascii'))
            a = self.execute("""SELECT DISTINCT {0} FROM "data"
                                WHERE phone = %s
                                ORDER BY lastname;
                                """.format(self.columns), (query,))

        elif query[0] == '(' and len(query) == 14: #US: (480) 555-1212
            query = query[1:4] + query[6:9] + query[10:14]
            a = self.execute("""SELECT DISTINCT {0} FROM "data"
                                WHERE phone = %s
                                ORDER BY lastname;
                                """.format(self.columns), (query,))

        elif query[0] == '+':  #International format
            trans = Translator(delete='+(-)./ ')
            query = trans(query.encode('ascii'))
            a = self.execute("""SELECT DISTINCT {0} FROM "data"
                                WHERE phone = %s
                                ORDER BY lastname;
                                """.format(self.columns), (query,))

        elif len(query) == 7:
            #Search by last seven:
            query = '%' + query
            a = self.execute("""SELECT DISTINCT {0} FROM "data"
                                WHERE phone LIKE %s
                                ORDER BY lastname;
                                """.format(self.columns), (query,))

        else:
            self.log.warn("Search key {0} probably isn't a phone number.")
            a = self.execute("""SELECT DISTINCT {0} FROM "data"
                                WHERE phone = %s
                                ORDER BY lastname;
                                """.format(self.columns), (query,))

        ret = []
        for i in a:
            ret.append(self.dict_factory(i)) #return as a nested dictionary
        return ret

    def SearchSecure(self, query):
        """
        Searches for a record by the security code assigned at check-in, if applicable.
        """
        a = self.execute("""SELECT DISTINCT {0} FROM data
                            INNER JOIN statistics ON data.id = statistics.person
                            WHERE statistics.code = %s;
                            """.format(self.columns), (query.upper(),))
        ret = []
        for i in a:
            ret.append(self.dict_factory(i)) #return as a nested dictionary
        return ret
    # === end search functions ===
    
    def GetRecordByID(self, ref):
        """
        Returns a single row specified by id.
        """
        a = self.execute("SELECT * FROM data WHERE id = %s", (ref,))
        
        ret = []
        for i in a:
            ret.append(self.dict_factory(i)) #return as a nested dictionary
        return ret[0]
    
    # === barcode functions ===
    def GetBarcodes(self, record):
        """
        Returns all barcodes listed for a given record ID.
        """
        a = self.execute("""SELECT DISTINCT id, value FROM barcode
                            WHERE ref = %s ORDER BY id;""", (record,))
        ret = []
        for i in a:
            ret.append(self.dict_factory(i)) #return as a nested dictionary
            #~ ret.append(i)
        return ret

    def AddBarcode(self, record, value):
        self.execute("""INSERT INTO barcode(value, ref)
                        VALUES (%s, %s);""", (value, record))

    def RemoveBarcode(self, ref):
        self.execute("DELETE FROM barcode WHERE id = %s;", (ref,))

    def RemoveAllBarcodes(self, ref):
        """
        Deletes all barcodes for a given record (nuke)
        """
        self.execute("DELETE FROM barcode WHERE ref = %s;", (ref,))

    def UpdateBarcode(self, ref, value):
        self.execute("UPDATE barcode SET value = %s WHERE id = %s", (value, ref))
    # === end barcode functions ===

    # === services functions ===
    def GetServices(self):
        a = self.execute("SELECT * FROM services ORDER BY id;")
        ret = []
        for i in a:
            ret.append(self.dict_factory(i)) #return as a nested dictionary
        return ret

    def AddService(self, name, day=0, time='00:00:00', endTime='23:59:59'):
        self.execute("""INSERT INTO services(name, day, time, "endTime")
                        VALUES (%s, %s, %s, %s);""", (name, day, time, endTime))

    def RemoveService(self, ref):
        self.execute("DELETE FROM services WHERE id = %s;", (ref,))

    def UpdateService(self, ref, name, day, time, endTime):
        self.execute("""UPDATE services SET name = %s,
                        day = %s, time = %s, "endTime" = %s WHERE id = %s;""",
                        (name, day, time, endTime, ref))
    # === end services functions ===
    
    # === activities functions ===
    def GetActivities(self):
        a = self.execute("SELECT * FROM activities;")
        ret = []
        for i in a:
            if i == None: i = u'—'
            ret.append(self.dict_factory(i)) #return as a nested dictionary
        return ret

    def GetActivity(self, ref):
        """
        Converts a reference to the activity table to an explicit string value
        (for reading a record's assigned activity with no forgein key support).
        """
        a = self.execute("SELECT name FROM activities WHERE id = %s;", (ref,))
        if len(a) > 0:
            return a[0][0]
        else:
            return None
            
    def GetActivityById(self, ref):
        a = self.execute("SELECT * FROM activities WHERE id = %s;", (ref,))
        if len(a) > 0:
            return self.dict_factory(a[0])
        else:
            return None
        

    def AddActivity(self, name, prefix='', securityTag=False, securityMode='simple',
                    nametag='default', nametagEnable=True,
                    parentTag='default', parentTagEnable=True, admin=None,
                    autoExpire = False, notifyExpire = False, newsletter=False,
                    newsletterLink='', parentURI='', alert=''):
        if prefix == '' or prefix == None:
            prefix = name[0].upper()
        self.execute("""INSERT INTO activities(name, prefix, "securityTag",
                        "securityMode", "nametagEnable", nametag,
                        "parentTagEnable", "parentTag", admin, "autoExpire",
                        "notifyExpire", newsletter, "newsletterLink",
                        "parentURI", "alertText")
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 
                        %s, %s, %s, %s, %s, %s);""",
                        (name, prefix, securityTag, securityMode,
                        nametagEnable, nametag, parentTagEnable, parentTag,
                        admin, autoExpire, notifyExpire, newsletter,
                        newsletterLink, parentURI, alert))

    def RemoveActivity(self, ref):
        self.execute("DELETE FROM activities WHERE id = %s;", (ref,))

    def UpdateActivity(self, ref, name, prefix, securityTag, securityMode,
                       nametag, nametagEnable, parentTag,
                       parentTagEnable, admin, autoExpire, notifyExpire,
                       newsletter, newsletterLink):
        if prefix == '' or prefix == None:
            prefix = name[0].upper()
        self.execute("""UPDATE activities SET name = %s, prefix = %s,
                        securityTag = %s, securityMode = %s,
                        nametag = %s, nametagEnable = %s, parentTag = %s,
                        parentTagEnable = %s, admin = %s, autoExpire = %s,
                        notifyExpire = %s, newsletter = %s,
                        newsletterLink = %s WHERE id = %s;""", (name, prefix,
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
        ret = self.execute('SELECT id FROM activities WHERE id = %s;',
            (activity,))
        if len(ret) == 1:
            #Activity exists.  Create room.
            self.execute("""INSERT INTO rooms(name, activity, "volunteerMinimum",
                            "maximumOccupancy", camera, "cameraFPS", admin,
                            "notifoUser", "notifoSecret", email, mobile, carrier)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                            (name, activity, volunteerMinimum, maximumOccupancy,
                            camera, cameraFPS, admin, notifoUser,
                            notifoSecret, email, mobile, carrier))
            return SUCCESS
        else:
            return CONSTRAINT_FAILED #Forgein key constraint failed

    def GetRooms(self):
        a = self.execute('SELECT * FROM rooms;')
        ret = []
        for i in a:
            ret.append(self.dict_factory(i)) #return as a nested dictionary
        return ret

    def GetRoomByID(self, ref):
        """
        Returns a room name specified from a reference (for displaying results).
        """
        a = self.execute('SELECT name FROM rooms WHERE id = %s;', (ref,))
        if a != None:
            try:
                return a[0][0] #Return string
            except IndexError:
                return ''
        else:
            return ''

    def GetRoom(self, activity):
        """
        Returns rooms dictionary matching a given activity (by name).
        """
        a = self.execute("""SELECT rooms.*
                            FROM rooms
                            INNER JOIN activities ON
                            activities.id = rooms.activity
                            WHERE activities.name = %s;""",
                            (activity,))
        ret = []
        for i in a:
            ret.append(self.dict_factory(i)) #return as a nested dictionary
        return ret

    def GetRoomID(self, name):
        """
        Return's a room's primary key (id) given a name.
        """
        a = self.execute("SELECT id FROM rooms WHERE name = %s;", (name,))
        if a != None:
            return a[0]
        else:
            return ''

    def RemoveRoom(self, ref):
        self.execute("DELETE FROM rooms WHERE id = %s;", (ref,))
    # === end room functions ===
    
    # === users functions ===
    def GetUsers(self):
        a = self.execute("""SELECT "user", admin, "notifoUser", "notifoSecret",
                            "scATR", "leftHanded", ref FROM users;""")
        return self.to_dict(a)

    def GetUser(self, user):
        #Should only return one row
        return self.to_dict(self.execute("SELECT * FROM users WHERE \"user\" = %s;", (user,)))[0]

    def UserExists(self, user):
        a = self.execute("SELECT id FROM \"users\" WHERE \"user\"= %s;", (user,))
        self.commit()
        if len(a) == 0:
            return False
        else:
            return True

    def AddUser(self, user, password, admin=False, notifoUser=None,
                notifoSecret=None, scATR=None, leftHanded=False, ref=None):
        #Check that the user doesn't exist:
        if len(self.execute("SELECT * FROM users WHERE user = %s;", \
          (user,))) != 0:
            self.commit()
            return USER_EXISTS

        salt = os.urandom(29).encode('base_64').strip('\n') #Get a salt
        if password == '': #Set a random password
            password = os.urandom(8).encode('base_64').strip('\n')
        ph = hashlib.sha256(password + salt)
        ph.hexdigest()

        try:
            self.execute("""INSERT INTO "users"("user", hash, salt, admin, "notifoUser",
                            "notifoSecret", "scATR", "leftHanded", ref) VALUES
                            (%s, %s, %s, %s, %s, %s, %s, %s, %s);""",
                            (user, ph.hexdigest(), salt, admin, notifoUser,
                            notifoSecret, scATR, leftHanded, ref))
        except psycopg2.IntegrityError:
            return USER_EXISTS
        finally:
            self.commit()
        return SUCCESS

    def RemoveUser(self, user):
        """
        Remove an user from the system by username.
        """
        self.execute("DELETE FROM users WHERE \"user\" = %s;", (user,))

    def AuthenticateUser(self, user, password):
        if self.UserExists(user):
            info = self.GetUser(user)
            passhash = hashlib.sha256(password + info['salt'])
            if info['hash'] == passhash.hexdigest():
                return 1
        return 0
    # == end users functions ==
    
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
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""", 
                    (person, str(datetime.date.today()), service, expiry,
                    datetime.datetime.now(), None, code, location, activity, room), 
                    cursor)
            #~ except sqlite.Error as e:
                #~ raise DatabaseError(UNKNOWN_ERROR, e.args[0])
                
        #~ #TODO: Incrament count, update last seen date.
        count = self.execute("SELECT count FROM data WHERE id = %s;", (person,))
        count = int(count[0][0]) + 1
        today = datetime.date.today()
        self.execute("UPDATE data SET count = %s, \"lastSeen\" = %s WHERE id = %s;", 
            (count, today, person))
        self.commit()

    def DoCheckout(self, person):
        """
        Marks a record as checked-out.
        """
        self.execute("UPDATE statistics SET checkout = %s WHERE person = %s AND \"date\" = date('now');",
            (datetime.datetime.now(), person))
        self.commit()
        
    # === end checkin functions ===
    
    def GetHistory(self, person):
        """
        Returns check-in history.
        """
        a = self.execute("SELECT date, service, checkin, checkout, room, location FROM statistics WHERE person = %s;", (person,))
        ret = []
        for i in a:
            ret.append(self.dict_factory(i)) #return as a nested dictionary
        return ret
    
    def GetStatus(self, ref, full=False):
        """
        Returns the check-in status for a specified record, according to the
        constants defined in taxidi.py. (STATUS_NONE, STATUS_CHECKED_IN, or
        STATUS_CHECKED_OUT).  If full=True, then the status is returned as part
        of a dictionary of the matching statistics row.  Only returns values from
        today's date.
        """
        a = self.execute("SELECT * FROM statistics WHERE person = %s AND checkin > date('now');", (ref,))
        ret = []
        for i in a:
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
            elif code == INVALID_PASSWORD:
                self.error = 'Invalid username, password, or authorization specification.'
        else:
            self.error = str(value).replace('\t', '').capitalize()
        self.code = code
    def __str__(self):
        return str(self.error).replace('\t', '').capitalize()
        #~ return repr(self.error)


if __name__ == '__main__':
    try:
        db = Database('localhost:15432', 'taxidi', 'taxidi', 'lamepass')
    except DatabaseError as e:
        print e.error
        exit()
        
    import pprint
    #~ newRecord = db.Register("Zac", "Sturgeon", "(212) 555-5555", "Diana Sturgeon")
    #~ db.Delete(newRecord)
    #~ print db.execute("SELECT * FROM \"data\";")
    #~ pprint.pprint( db.Search('sturgeon') )
    #~ db.Update(12, "Zachary", "Sturgeon", "(212) 555-5555", "James Sturgeon")
    
    #Barcode functions:
    #~ db.AddBarcode(1, '12345')
    #~ db.RemoveBarcode(1)
    #~ pprint.pprint(db.Search("ABCD"))
    #~ codes = db.GetBarcodes(2)
    #~ pprint.pprint(codes)
    #~ print
    #~ print [ a['value'] for a in codes ]
    
    print db.Search("9989")
    
    #Services:
    #~ db.AddService('First Service')
    #~ print db.GetServices()
    
    #Activities:
    #~ db.AddActivity('Explorers', securityTag=True, securityMode='md5', 
                    #~ nametagEnable=True, parentTagEnable=True,
                    #~ alert='Nursery alert text goes here.')
    #~ db.AddActivity('Outfitters', securityTag=False, securityMode='simple', 
                    #~ nametagEnable=True, parentTagEnable=False,
                    #~ alert='Nursery alert text goes here.')
    #~ db.commit()
    #~ print db.GetActivityById(1)
    
    #User functions:
    #~ db.RemoveUser('admin')
    #~ db.commit()
    #~ if db.AddUser('admin', 'password', admin=True) == USER_EXISTS: print "User admin already exists"
    #~ db.commit()
    #~ pprint.pprint( db.GetUsers() )
    #~ print
    #~ print (db.AuthenticateUser('admin', 'badpassword') == AUTHORIZED) #False
    #~ print (db.AuthenticateUser('baduser', 'pass') == AUTHORIZED)      #False
    #~ print (db.AuthenticateUser(u'admin', u'password') == AUTHORIZED)    #True
    #~ print (db.AuthenticateUser('admin', 'password') == AUTHORIZED)    #True
    
    #Check-in:
    #~ db.DoCheckin(2, ('First Service', 'Second Service', 'Third Service'), 
                 #~ '14:59:59', '5C55', 'Kiosk1', 'Explorers', 'Jungle Room')
                 
    #Rooms:
    #~ db.AddRoom("Bunnies", 1)
    #~ db.AddRoom("Ducks", 1)
    #~ db.AddRoom("Kittens", 1)
    #~ db.AddRoom("Robins", 1)
    #~ db.AddRoom("Squirrels", 1)
    #~ db.AddRoom("Puppies", 1)
    #~ db.AddRoom("Caterpillars", 1)
    #~ db.AddRoom("Butterflies", 1)
    #~ db.AddRoom("Turtles", 1)
    #~ db.AddRoom("Frogs", 1)
    #~ db.AddRoom("Outfitters", 2)
    
    #~ pprint.pprint(db.GetRoomByID(8))
    pprint.pprint(db.GetHistory(1))
    
    db.commit()

