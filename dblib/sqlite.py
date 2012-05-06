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

#TODO:
# - Code to check if database file is writeable
# - Implement fulltext search extension.
# - Combine phone fields and allow for international formats?
#       ¤ Still perform search by last n digits
#       ¤ Phone as text; '334|832|1234' '015225428548' '+49|1606128338'
#       ¤ Mask options: US, International, No formatting (numbers only)
#       ¤ > SELECT ... WHERE phone LIKE '%'+Query
# - Check if tables exists before continuing?  No table checking for now.
# - Timer to automatically commit records after 'n' seconds (?)

import os
import logging
import time
import datetime
import sqlite3 as sqlite

SUCCESS = 1
FAIL = 2
EMPTY_RESULT = 4

class Database:
    """SQLite3 driver class for taxídí database."""
    def __init__(self, file, log=''):
        """
        Open connections to sqlite file; create if it doesn't exist.
        Takes a file and optional logger handler as init arugments.
        """

        self.debug = True
        #what columns will be returned when SELECT * is issued. Keeps things from breaking.
        self.columns = """data.id, name, lastname, dob, activity room, grade, phone,
                          mobileCarrier, paging, parent1, parent1Link, parent2,
                          parent2Link, parentEmail, medical, joinDate, lastSeen,
                          lastModified, count, visitor, noParentTag, barcode,
                          picture, authorized, unauthorized, notes"""

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

        file = os.path.expanduser(file)
        self.log.debug('Attempting to open sqlite3 database at {0}'.format(file))
        #check if file exists/is readable
        try:
            fh = open(file, 'r')
            fh.close()
        except IOError as e:
            self.log.warn('({0})'.format(e))
            #file does not exist: Create table
            self.conn = sqlite.connect(file)
            self.conn.text_factory = str #use unicode strings
            self.cursor = self.conn.cursor()
            self.createTables()
            self.conn.commit()
            self.conn.close()

        #check if database can be written to (modification/creation)
        if not os.access(file, os.W_OK):
            self.log.critical(
                'the file {} does not have write permissions!'.format(file))
            self.log.critical('Unable to open database.')
            return 127 #Causes TypeException in the calling module.

        #open database for writing and query
        self.conn = sqlite.connect(file)
        self.cursor = self.conn.cursor()
        self.log.info("Created sqlite3 database instance using file '{}'".
            format(file))

    def createTables(self):
        """
        Initializes the database, creating required tables.
        """
        self.log.warning('Tables did not exist. Creating...')
        #main data
        self.execute("""CREATE TABLE data(id integer primary key,
            name text, lastname text,  dob text, activity integer,
            room integer, grade string, phone string,
            mobileCarrier integer, paging text, parent1 text,
            parent2 text, parent1Link text, parent2Link text,
            parentEmail text, medical text, joinDate text,
            lastSeen text, lastModified text, count integer,
            visitor integer, noParentTag integer,
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
            mobileCarrier integer, backgroundCheck integer,
            backgroundDocuments text, profession text, title text,
            company text, jobContact text, address text, city text,
            zip text, state text, country text, nametag integer,
            category text, subtitle text, services text, rooms text,
            notifoUser text, notifoSecret text,
            availability text, joinDate text, lastSeen text,
            lastModified text, picture text, notes text);""")
        #categories
        self.execute("""CREATE TABLE categories(id integer primary key,
            name text, admin integer);""")
        #users
        self.execute("""CREATE TABLE users(id integer primary key,
            user text, hash text, salt text, admin integer,
            notifoUser text, notifoSecret text,
            leftHanded integer, ref integer);""")
        #activities
        self.execute("""CREATE TABLE activities(id integer primary key,
            prefix text, securityTag text, securityMode text, theme text,
            nametagEnable integer, nametag text,
            parentTagEnable integer, parentTag text);""")
        #services
        self.execute("""CREATE TABLE services(id integer primary key,
            name text, day integer, time text);""")
        #rooms
        self.execute("""CREATE TABLE rooms(id integer primary key,
            name text, volunteerMinimum integer,
            maximumOccupancy integer, camera text, cameraFPS integer,
            admin integer, email text, mobile text, carrier integer);""")
        #carriers
        self.execute("""CREATE TABLE carriers(id integer primary key,
            name text, region text, address text, subject text,
            message text);""")
        #statistics
        self.execute("""CREATE TABLE statistics(id integer primary key,
            person integer, date text,
            services forgein key references services(id),
            checkin text, checkout text, code text, location text,
            volunteer integer);""")
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
            visitor=False, noParentTag=False, barcode=None, picture='',
            authorized=None, unauthorized=None, notes=''):
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
            lastModified = time.ctime() #should be plain ISO format, only for reporting

        #escape and execute
        self.execute("""INSERT INTO data(name, lastname, dob, phone,
        primaryKey, parent1, mobileCarrier, activity, room, grade,
        parent2, parent1Link, parent2Link, parentEmail, medical,
        joinDate, lastSeen, lastModified, count, visitor, noParentTag,
        barcode, picture, notes) VALUES
        (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);""",
        [name, lastname, dob, phone, primaryKey, parent1, mobileCarrier,
        activity, room, grade, parent2, parent1Link, parent2Link,
        parentEmail, medical, joinDate, lastSeen, lastModified, count,
        int(visitor), int(noParentTag), barcode, picture, notes])

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
        self.execute("DELETE FROM data WHERE id = ?;", (index))

    def Update(self, index, name, lastname, dob, phone, primaryKey,
            parent1, mobileCarrier=0, activity=0, room=0, grade='',
            parent2='', parent1Link='', parent2Link='', parentEmail='',
            medical='', joinDate='', lastSeen='', visitor=False,
            noParentTag=False, barcode='', picture='', notes=''):
        """Update a record.  Pass index as first argument.  lastModified automatically set.

        name, lastname, dob, phone, primaryKey, and parent1 are mandatory.
        Defaults are as follows: mobileCarrier=0, activity=0, room=0, grade='',
        parent2='', parent1Link='', parent2Link='', parentEmail='', medical='',
        joinDate='', lastSeen='', visitor=False,
        noParentTag=False, barcode='', picture='',  notes=''
        """
        self.execute("UPDATE data SET name=?, lastname=? WHERE id=?;", (name, lastname, index))
        self.execute("UPDATE data SET dob=? WHERE id=?;", (dob, index))
        self.execute("UPDATE data SET phone=?, primarykey=? WHERE id=?;",(phone, primaryKey, index))
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
        self.execute("""UPDATE data SET visitor=?, noParentTag=?, barcode=?,
            picture=?, notes=? WHERE id=?;""", (int(visitor), int(noParentTag),
            barcode, picture, notes, index))

    #return all entries (for browsing)
    def GetAll(self):
        """Returns all rows. (useful for browsing)"""
        return self.execute("SELECT * FROM data;").fetchall()


    def Search(self, query):
        """Generic search function.

        Searches first through `data`, then passes to SearchVolunteer()
        Accepts query as first argument.  Searches the following in order:
        - Last four digits of phone number (if len == 4)
        - primaryKey
        - lastname
        - firstname
        """
        if len(query) == 4:
            pass

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
                                OR parent2 = ? COLLATE NOCASE;
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
                            INNER JOIN barcode ON data.barcode = barcode.ref
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
        #TODO: Search by secure code
        pass


    # == end data functions ==

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

        if lastModified == '':
            lastModified == time.ctime() #should be plain ISO format

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
        return self.execute("SELECT * FROM categories;")

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
        self.execute("UPDATE categories SET name = ? WHERE id = ?;",
            (name, admin))

    # == end categories ==


    # == generic SQL functions ==
    def execute(self, sql, args=('')):
        """Executes SQL, reporting debug to the log. For internal use."""
        if self.debug:
            sql = sql.replace('    ', '').replace('\n', ' ')  #make it pretty
            self.log.debug((sql, args))
        try:
            data = self.cursor.execute(sql, args)
            return data
        except sqlite.OperationalError as e:
            self.log.error('SQLite3 returned operational error: {}'
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

    # == end generic functions ==

class DatabaseError(Exception):
    def __init__(self, code, value=''):
        if value == '':
            self.error = 'Generic database error.'
            if code == EMPTY_RESULT:
                self.error = 'Query returned empty result'
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
        #~ db = Database('~/.taxidi/database/users.db')
        db = Database('~/test.db')
    except TypeError:
        print 'Unable to open database (file write-protected?)'
        #display an error dialogue and exit
    #~ print db.SearchName('Gal*')
    print db.SearchBarcode('1234')
    #~ print db.SearchPhone('7916')
