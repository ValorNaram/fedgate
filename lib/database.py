#!/usr/bin/env python3
from psycopg2 import sql
import psycopg2
class helper():
	def __init__(self, conf):
		self.conf = conf
		self.conn = psycopg2.connect(conf["dbconnstr"])
		self.lock = False
		self.canShutdown = True
	
	def __toJSON(self, table, columns, curs):
		data = {}
		if curs.rowcount == 0:
			return data
		for row in table:
			col = {}
			ident = ""
			for i in range(0, len(columns)):
				if columns[i] == "id":
					ident = row[i]
				col[columns[i]] = row[i]
			data[ident] = col
		return data
	
	def modifyUser(self, userid, name, param):
		output = ""
		if name in self.conf:
			query = self.conf[name]
			cur = self.conn.cursor()
			output = cur.mogrify(query, (param, userid)).decode("utf-8")
			cur.close()
		return output
	
	def userExists(self, userid, table):
		result = False
		query = "SELECT * FROM {} WHERE id=%s".format(table)
		cur = self.conn.cursor()
		
		cur.execute(query, (userid,))
		if cur.rowcount == 1:
			result = True
		else:
			result = False
		cur.close()
		return result
	
	def tableSchema(self, tablename):
		output = []
		query = "select column_name from information_schema.columns where table_name=%s;"
		
		cur = self.conn.cursor()
		cur.execute(query, (tablename,))
		data = cur.fetchall()
		cur.close()
		
		for row in data:
			if not row[0] == "id":
				output.append(row[0])
		
		return output
	
	def searchpeople(self, filters):
		searchQuery = self.conf["search"]
		filterQuery = []
		
		cur = self.conn.cursor()
		for fltr in filters:
			if "search_" + fltr in self.conf and not fltr == "id":
				value = filters[fltr]
				query = self.conf["search_" + fltr]
				if type(value) is list:
					for v in value:
						if query.find("%s") > -1:
							filterQuery.append(cur.mogrify(query, (v,)).decode("utf-8"))
						else:
							filerQuery.append(query)
				else:
					if query.find("%s") > -1:
						filterQuery.append(cur.mogrify(query, (value,)).decode("utf-8"))
					else:
						filterQuery.append(query)
		cur.close()
		return searchQuery + " " + " AND ".join(filterQuery) + ";"
	
	def sendToPostgres(self, query, params=(), limit=20):
		if self.lock == False:
			output = {}
			self.canShutdown = False
			
			with self.conn:
				with self.conn.cursor() as cursor:
					if params == ():
						cursor.execute(query)
					else:
						cursor.execute(query, params)
					if not cursor.description == None:
						columns = []
						for col in cursor.description:
							columns.append(col.name)
						output = self.__toJSON(cursor.fetchmany(limit), columns, cursor)
			
			self.canShutdown = True
			return output
		else:
			return "error - shutting down"
	
	def tearDown(self):
		self.lock = True
		while self.canShutdown == False:
			pass
		self.conn.close()

class management():
	def __init__(self, dbconnstr):
		self.error = ""
		try:
			self.conn = psycopg2.connect(dbconnstr)
		except psycopg2.errors.OperationalError:
			self.error = "DOES NOT EXIST"
	
	def alterTable(self, name, desiredCols, beloud=True):
		query = []
		returnedCols = []
		desiredCols_simplified = []
		changes = False
		
		if not ("id", "text") in desiredCols:
			desiredCols = [("id", "text")] + desiredCols
		
		for i in desiredCols:
			desiredCols_simplified.append(i[0])
		
		with self.conn:
			with self.conn.cursor() as cursor:
				cursor.execute(sql.SQL("SELECT * FROM {} LIMIT 0").format(sql.Identifier(name)))
				for col in cursor.description:
					returnedCols.append(col.name)
		
		for n, i in enumerate(returnedCols):
			colname = i[0]
			if colname in returnedCols and not colname in desiredCols_simplified:
				# remove from database table `name`
				if beloud:
					print("\033[1;31mwill remove\033[0;m '{}' from database table '{}'".format(i, name))
				
				cur = self.conn.cursor()
				query.append(sql.SQL("ALTER TABLE {} DROP COLUMN {}").format(sql.Identifier(name), sql.Identifier(colname)).as_string(cur))
				cur.close()
				changes = True
		for n, i in enumerate(desiredCols):
			colname, coltype = i
			if colname in desiredCols_simplified and not colname in returnedCols:
				# add to database table `name`
				if beloud:
					print("\033[1;32mwill add\033[0;m '{}' to database table '{}'".format(i, name))
				
				cur = self.conn.cursor()
				print(colname, coltype)
				query.append(sql.SQL("ALTER TABLE {} ADD {} {}").format(sql.Identifier(name), sql.Identifier(colname), sql.Identifier(coltype)).as_string(cur))
				cur.close()
				changes = True
		
		if len(query) > 0:
			with self.conn:
				with self.conn.cursor() as cursor:
					print("executing query ('will' becomes 'do now')...")
					cursor.execute(";\n".join(query))
		return changes
	
	def executeCMD(self, query, params=()):
		error = None
		with self.conn:
			with self.conn.cursor() as cursor:
				try:
					cursor.execute(query, params)
				except Exception as e:
					error = e
					cursor.rollback()
		return error
				
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
