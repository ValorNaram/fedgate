#!/usr/bin/env python3
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extensions import ISOLATION_LEVEL_DEFAULT
from psycopg2 import sql
import psycopg2, uuid, logging, signal

class Management():
	def __log(self, m):
		if self.beloud:
			logging.info(m)
	
	def __init__(self, dbconnstr, beloud=True):
		self.error = ""
		self.beloud = beloud
		try:
			self.conn = psycopg2.connect(dbconnstr)
		except psycopg2.errors.OperationalError:
			self.error = "DOES NOT EXIST"
	
	def createDatabase(self, dbname):
		self.__log("Attempting to create database '{}' with owner '{}'".format(dbname, os.environ["USER"]))
		self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
		
		cur = self.conn.cursor()
		cur.execute("CREATE DATABASE {} WITH OWNER '{}'".format(dbname, os.environ["USER"]))
		cur.close()
		
		self.conn.set_isolation_level(ISOLATION_LEVEL_DEFAULT)
	
	def alterTable(self, name, desiredCols, execute=True):
		query = []
		returnedCols = []
		desiredCols_simplified = []
		changes = False
		
		for i in desiredCols:
			desiredCols_simplified.append(i[0])
		
		# find existing columns for table `name` (if any)
		with self.conn:
			with self.conn.cursor() as cursor:
				cursor.execute(sql.SQL("SELECT * FROM {} LIMIT 0").format(sql.Identifier(name)))
				for col in cursor.description:
					returnedCols.append(col.name)
		
		# find columns in the database table `name` which do not exist in the table specification
		for n, i in enumerate(returnedCols):
			colname = i[0]
			if colname in returnedCols and not colname in desiredCols_simplified:
				# remove from database table `name`
				self.__log("\033[1;31mwill remove\033[0;m '{}' from database table '{}'".format(i, name))
				
				cur = self.conn.cursor()
				query.append(sql.SQL("ALTER TABLE {} DROP COLUMN {}").format(sql.Identifier(name), sql.Identifier(colname)).as_string(cur))
				cur.close()
				changes = True
		# find columns in the table specification which do not exist in the database table `name`
		for n, i in enumerate(desiredCols):
			colname, coltype = i
			if colname in desiredCols_simplified and not colname in returnedCols:
				# add to database table `name`
				self.__log("\033[1;32mwill add\033[0;m '{}' to database table '{}'".format(i, name))
				
				cur = self.conn.cursor()
				query.append(sql.SQL("ALTER TABLE {} ADD {} {}").format(sql.Identifier(name), sql.Identifier(colname), sql.Identifier(coltype)).as_string(cur))
				cur.close()
				changes = True
		
		if not execute:
			return changes, query # in boolean (true, if any changes need to happen) and the query/queries as a list of query strings 
		if len(query) > 0:
			with self.conn:
				with self.conn.cursor() as cursor:
					self.__log("executing query ('will' becomes 'do now')...")
					cursor.execute(";\n".join(query))
		return changes
	
	def executeCMD(self, query, params=()):
		error = None
		with self.conn:
			with self.conn.cursor() as cursor:
				try:
					cursor.execute(query, params)
				except Exception as e:
					self.error = e
					cursor.rollback()
		return error
	
	def createTable(self, name, columns):
		return self.executeCMD(sql.SQL("CREATE TABLE {} ({})".format(sql.Identifier(name), ",\n".join(columns))))
				
	def tableExists(self, name):
		exists = False
		with self.conn:
			with self.conn.cursor() as cursor:
				try:
					cursor.execute("SELECT * FROM " + name + " LIMIT 0")
					exists = True
				except psycopg2.errors.UndefinedTable:
					exists = False
		return exists
	
	def tearDown(self):
		self.conn.close()

class Initiator():
	def __log(self m):
		if self.beloud:
			logging.info(m)
	
	def database(self):
		dbhelper = Management(self.dbconnstr)
		
		if not dbhelper.error == "":
			self.__log("\033[1;mDatabase does not exist or another error occurred\033[0;m")
			signal.signal(15)
		
		self.__log("checking existence of required tables...")
		for table in self.tables:
			if dbhelper.tableExists(table):
				self.__log("\033[0;32m Table '{}' exists...\033[0;m".format(table))
			else:
				self.__log("\033[0;31m Table '{}' does not exist!\033[0;m Creating it...".format(table))
				dbhelper.createTable(table, self.tables[table])
			
		self.__log("syncing columns (insert/remove)...")
		for i in self.conf["tables"]:
			if "table_" + i in self.conf:
				cols = copy.copy(self.conf["table_" + i])
				for n, content in enumerate(cols):
					colname, coltype = content.split(" ")
					cols[n] = (colname, coltype)
				dbhelper.alterTable(i, cols)
	
		self.__log("disconnecting from database...")
		dbhelper.tearDown()
	
	def __init__(self, tables, dbconnstr, beloud=True):
		"""
		Creates the Initiator() class object dealing as a wrapper for database object creation options invoking methods of the Management() class internally. It requires the following non-optional arguments:
		`tables`: Takes a dict containing the table name to create the table under as the key and as a value a list of strings for the column names and their parameters. Example: {"table1": ["column1 uuid", "column2 int", "column3 text"], "table2": [...], ...}
		`dbconnstr`: A string defining the connection following the specification at https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING
		
		And taking the following optional non-required arguments:
		`beloud`: Boolean attribute specifying the verbosity of the methods of this class. Default: True
		"""
		self.tables = tables
		self.dbconnstr = dbconnstr
		self.beloud = beloud
