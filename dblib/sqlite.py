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

class Database:
    """SQLite3 driver class for taxídí database."""
    def __init__(self, file, log=''):
        """
        Open connections to sqlite file; create if it doesn't exist.
        Takes a file and optional logger handler as init arugments.
        """

        #convert $log to global if a handle was passed:
        if log:
            global logger
            logger = log

        #check if file exists/is readable
        try:
            fh = open(file, 'r')
            fh.close()
        except IOError as e:
            logger.warn('({0})'.format(e))
            #file does not exist: Create table
            self.conn = sqlite.connect(file)
            self.conn.text_factory = str #use unicode strings
            self.cursor = self.conn.cursor()
            self.createTables()
            self.conn.commit()
            self.conn.close()

        #check if database can be written to (modification/creation)
        if not os.access(file, os.W_OK):
            logger.critical(
                'the file {} does not have write permissions!'.format(file))
            logger.critical('Unable to open database.')
            return 127 #Causes TypeException in the calling module.

        #open database for writing and query
        self.conn = sqlite.connect(file)
        self.cursor = self.conn.cursor()
        logger.info("Created sqlite3 database instance using file '{}'".
            format(file))

    def createTables(self):
        """Initializes the database, creating required tables."""
        logger.warning('Tables did not exist. Creating...')
        #main data
        self.execute("""CREATE TABLE data(id integer primary key,
            name text, lastname text,  dob text, activity integer,
            room integer, grade string, phone string,
            mobileCarrier integer, primaryKey text, parent1 text,
            parent2 text, parent1Link text, parent2Link text,
            parentEmail text, medical text, joinDate text,
            lastSeen text, lastModified text, count integer,
            visitor integer, noParentTag integer,
            barcode string, picture text, notes text);""")
        #volunteers
        self.execute("""CREATE TABLE volunteers(id integer primary key,
            name text, lastname text, dob text, email text,
            username text, phoneHome text, phoneMobile text,
            mobileCarrier integer, backgroundCheck integer,
            backgroundDocuments text, profession text, title text,
            company text, jobContact text, address text, city text,
            zip text, state text, country text, nametag integer,
            category text, subtitle text, services text, rooms text,
            availability text, joinDate text, lastSeen text,
            lastModified text, picture text, notes text);""")
        #categories
        self.execute("""CREATE TABLE categories(id integer primary key,
            name text, admin integer);""")
        #users
        self.execute("""CREATE TABLE users(id integer primary key,
            user text, hash text, salt text, admin integer);""")
        #activities
        self.execute("""CREATE TABLE activities(id integer primary key,
            name text, theme text);""")
        #services
        self.execute("""CREATE TABLE services(id integer primary key,
            name text, day integer, time);""")
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
            person integer, date text, time text, location text,
            volunteer integer);""")
        logger.info('Tables created')
        self.conn.commit()
        logger.debug('Tables committed to database')
        return 0

    # == End __init__  ==


    # == data functions ==
    # Populate all fields for registering a child only. Entries without
    #   a default are mandatory.  Form should check for missing stuff.
    def Register(self, name, lastname, dob, phone, primaryKey, parent1,
            mobileCarrier=0, activity=0, room=0, grade='', parent2='',
            parent1Link='', parent2Link='', parentEmail='',
            medical='', joinDate='', lastSeen='', lastModified='',
            visitor=False, noParentTag=False, barcode='', picture='',
            notes=''):
        """Enter a new child's record into the data table.

        name, lastname, dob, phone, primaryKey, and parent1 are mandatory.
        Defaults are as follows: mobileCarrier=0, activity=0, room=0, grade='',
        parent2='', parent1Link='', parent2Link='', parentEmail='', medical='',
        joinDate='', lastSeen='', lastModified='', visitor=False,
        noParentTag=False, barcode='', picture='',  notes=''
        """

        #set dates:
        if joinDate == '': #Generally should always be true (unless
            joinDate = str(datetime.date.today()) #importing from script

        if lastSeen == '':
            lastSeen = datetime.date.today()

        if lastModified == '':
            lastModified = time.ctime() #should be plain ISO format

        count = 0 #should always be nil; no check-ins yet.
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

    def Delete(self, index):
        """Delete a row in the data table by index."""
        self.execute("DELETE FROM data WHERE id = ?;", [index])

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
        return self.execute("SELECT * FROM data;")


    def Search(self, query):
        """Generic search function.

        Searches first through `data`, then passes to SearchVolunteer()
        Accepts query as first argument.  Searches the following in order:
        - Last four digits of phone number (if len == 4)
        - primaryKey
        - lastname
        - firstname
        """

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
            logger.warning("Deleting all rows in table 'categories'")
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
        sql = sql.replace('    ', '').replace('\n', ' ')  #make it pretty
        logger.debug((sql, args))
        try:
            data = self.cursor.execute(sql, args)
            return data.fetchall()
        except sqlite.OperationalError as e:
            logger.error('SQLite3 returned operational error: {}'
                .format(e))
            if self.conn:
                self.conn.rollback()    #drop any changes to preserve db.

    #To keep things speedy we need to be able to commit from the calling module
    def commit(self):
        """Commit SQL to the database. Use sparingly for best performance."""
        logger.debug('Committed database')
        return self.conn.commit()   # Should be used sparingly otherwise

    # == end generic functions ==
