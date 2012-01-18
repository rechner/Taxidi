#!/usr/bin/env python
#-*- coding:utf-8 -*-

# User Fields:  Name, lName, DoB, Activity, Room, Grade, Phone, 
#(Mobile? as bool), MobileCarrier, Primary, Parent1, Parent2, 
#ParentEmail, Medical, JoinDate, LastSeen, Count, Barcode, Picture, Notes

#TODO:
# - Code to check if database file is writeable
# - Combine phone fields and allow for international formats
#		¤ Still perform search by last n digits
#		¤ Phone as text; '334|832|1234' '015225428548' '+49|1606128338'
#		¤ Mask options: US, International, No formatting (numbers only)
#		¤ > SELECT ... WHERE phone LIKE '%'+Query

import os
import logging
import sqlite3 as sqlite

class Database:
	"""SQLite3 driver class for taxídí database."""
	def __init__(self, file, log=''):
		"""
		Open connections to sqlite file; create if it doesn't exist.
		Takes a file and optional loger handler as init arugments.
		"""
		
		#convert $log to global if a handle was passed:
		if log:
			global logger
			logger = log
		
		#check if file exists/is readable
		try:
			fh = open(file)
			fh.close()
		except IOError as e:
			logger.warn('({0})'.format(e))
			#file does not exist: Create table
			self.conn = sqlite.connect(file)
			self.cursor = self.conn.cursor()
			self.CreateTables()
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
		
		
	def CreateTables(self):
		logger.warning('Tables did not exist. Creating...')
		self.execute("""CREATE TABLE data(id integer primary key, 
			Name text, lName text, DoB text, Activity integer, 
			Room integer, Grade text, Phone integer, Mobile bool, 
			MobileCarrier integer, PrimaryKey text, Parent1 text, 
			Parent2 text, ParentEmail text, Medical text, 
			JoinDate text, LastSeen text, Count integer, Barcode text, 
			Picture text, Notes text);""")
		logger.info('Tables created')
		return 0
		
	def execute(self, sql):
		logger.debug(sql)
		self.cursor.execute(sql)


