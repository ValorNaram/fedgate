#!/usr/bin/env python3
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extensions import ISOLATION_LEVEL_DEFAULT
from psycopg2 import sql
import psycopg2, uuid

class Record():
	def __toDict(self, table):
		data = {}
		index = 0
		if self.cur.rowcount == 0:
			return data
		
		for row in table:
			col = {}
			for i in range(0, len(self.columns)):
				col[self.columns[i]] = row[i]
			data[index] = col
			index += 1
		return data
	
	def __init__(self, conn, query, params=(), limit=1):
		self.conn = conn
		self.cur = self.conn.cursor()
		self.limit = limit
		
		if params == ():
			self.cur.execute(query)
		else:
			self.cur.execute(query, params)
		
		self.columns = []
		if not self.cur.description == None:
			for col in self.cur.description:
				self.columns.append(col.name)
		
	def __iter__(self):
		return self
	
	def __next__(self):
		if self.limit == 1:
			result = self.cur.fetchone()
			if result == None:
				self.cur.close()
				raise StopIteration
			
			return self.__toDict([result])[0]
		else:
			result = self.cur.fetchmany(self.limit)
			if result == None:
				self.cur.close()
				raise StopIteration
			
			return self.__toDict(result)
	
	def cancel(self):
		self.cur.close()
	
	def get(self):
		result = {}
		
		try:
			result = self.__next__()
		except StopIteration:
			pass
		
		self.cancel()
		return result
	def status(self):
		return self.cur.statusmessage

class management(): # not thread safe
	def __init__(self, dbconnstr):
		self.error = ""
		try:
			self.conn = psycopg2.connect(dbconnstr)
		except psycopg2.errors.OperationalError:
			self.error = "DOES NOT EXIST"
	
	def createDatabase(self, dbname):
		self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
		cur = self.conn.cursor()
		cur.execute("CREATE DATABASE {} WITH OWNER '{}'".format(dbname, os.environ["USER"]))
		cur.close()
		self.conn.set_isolation_level(ISOLATION_LEVEL_DEFAULT)
	
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


class Driver():
	def __initDB(self):
		dbhelper = management(APIconf["dbconnstr"])
		if not dbhelper.error == "":
			logging.info("\033[1;mDatabase does not exist\033[0;m")
			
			logging.info("creating database '{}'...".format(APIconf["dbname"]))
			os.system(cmds["createdb"].format(APIconf["dbname"]))
		
			logging.info("restarting...")
			return main()
		else:
			logging.info("\033[1;mDatabase does exist\033[0;m")
		
		logging.info("checking existence of requirred tables...")
		for i in queries:
			if dbhelper.tableExists(i):
				logging.info("\033[0;32m  '{}' exists...\033[0;m".format(i))
			else:
				logging.info("\033[0;31m  '{}' does not exist\033[0;m".format(i))
				if "table_" + i in APIconf:
					logging.info("  creating table '{}'...".format(i))
					dbhelper.executeCMD(sqls[queries[i]].format(i, ",\n".join(APIconf["table_" + i])))
				else:
					logging.info("\033[0;31mtable scheme not specified in mentorapi.yml!\033[0;m")
			
		logging.info("syncing columns (insert/remove)...")
		changes = False
		for i in queries:
			if "table_" + i in APIconf:
				cols = copy.copy(APIconf["table_" + i])
				for n, content in enumerate(cols):
					colname, coltype = content.split(" ")
					cols[n] = (colname, coltype)
				changes = dbhelper.alterTable(i, cols)
	
		logging.info("generating select statement for the view creation query...")
		select = []
		select2 = []
		for i in queries:
			confname = "table_" + i
			if confname in APIconf:
				for content in APIconf[confname]:
					content = content.split(" ")
					if not content[0] in select2:
						select.append(i + "." + content[0])
						select2.append(content[0])
	
		logging.info("inserting generated select statement and execute query...")
		logging.info("View creation query: \033[0;33m" + sqls["createview"].format(", ".join(select)) + "\033[0;m")
		if changes or dbhelper.tableExists("userdetails"):
			logging.info("dropping view first...")
			dbhelper.executeCMD(sqls["deleteview"])
			logging.info("executing generated select statement...")
		dbhelper.executeCMD(sqls["createview"].format(", ".join(select)))
	
		logging.info("disconnecting from database...")
		dbhelper.tearDown()

	def __init__(self, conf):
		self.conf = conf
		self.psqlconf = self.conf["postgresql"]
		self.tablespecifiedby = self.conf["fieldrepresentsatable"]
		self.primaryfield = self.conf["primaryfield"]
		
		logging.info("connecting to postgresql database...")
		try:
			self.conn = psycopg2.connect(self.psqlconf["dbconnstr"])
		except psycopg2.errors.OperationalError:
			self.error = psycopg2.errors.OperationalError
		
		self.name = "PostgreSQL driver for FedGate"
		self.version = "1.0"
		self.description = "Allows the FedGate instance to use postgres as a storage engine. This is a non-relational database"
		self.author = "Sören Reinecke alias Valor Nara
	
	def validateReadAction(self, func):
		def func_wrapper(json):
			for i in self.conf["mandatoryfields"]:
				if not i in json: # if a mandatory field hasn't been supplied by the client, then
					return {} # return an empty result set.
			
			if not self.tablespecifiedby in json: # if the table name specifier hasn't been supplied by the client, then
				return {} # return an empty result set.
			func(json)
		return func_wrapper
	
	def validateWriteAction(self, func):
		def dummyFunc(json):
			return {"survivedValidator": True} # means that client's input survived the validator we call below and pass in this function
		
		def func_wrapper(json):
			valInp = validateReadAction(dummyFunc) # calling 'validateReadAction' decorator and passing it a function which does nothing so our function we want to validate does not get called by the callee while we are not finish doing validation
			result = valInp(json) # validate the 'json' python3 dictionary input using the validator 'validateReadAction'
			
			if not self.primaryfield in json and not len(result) == 0: # if the primary key for the primary field to send with that write request hasn't been supplied by the client and the validator we called above does not return any result, then
				return {} # return an empty result set.
			func(json)
		return func_wrapper
	
	@validateReadAction()
	def getEntries(json):
		query = ["SELECT * FROM {}"]
		params = []
		
		for i in json:
			query.append(self.psqlconf["querybyfield"][i])
			params.append(json[i])
		
		query.append("LIMIT {} ORDER BY {} DESC".format(self.conf["fetchrows"], self.conf["orderbyfield"]))
		
		if "pagination" in json:
			query.append("OFFSET %s ROWS")
			params.append(json["pagination"]["from"])
			
			query.append("FETCH NEXT %s ROWS ONLY")
			params.append(json["pagination"]["to"])
			
			del json["pagination"]
		
		
		return Record(self.conn, sql.SQL(" ".join(query) + ";").format(sql.Identifier(json[self.tablespecifiedby])), tuple(params)).get()
	
	@validateWriteAction()
	def changeEntry(json):
		query = ["UPDATE {}", "SET"]
		formatting = [sql.Identifier(json[self.tablespecifiedby])]
		params = []
		
		primevalue = json[self.primaryfield]
		del json[self.primaryfield]
		
		for i in json:
			if len(query) == 2:
				query.append("{} = %s")
			else:
				query.append(", {} = %s")
			formatting.append(sql.Identifier(i))
			params.append(json[i])
		
		query.append("WHERE {} = %s")
		formatting.append(sql.Identifier(self.primaryfield))
		params.append(primevalue)
		
		Record(self.conn, sql.SQL(" ".join(query) + ";").format(tuple(formatting)), tuple(params)).get()
	
	@validateWriteAction()
	def addEntry(json):
		query = ["INSERT INTO {} ("]
		formatting = []
		params = []
		columns = []
		
		json[self.primaryfield] = str(uuid.uuid4())
		
		for i in self.conf["TABLE_" + json[self.tablespecifiedby]]
			columns.append(i.split(" ", 1)[0])
		
		def dummyAdd(char, toList):
			for i in columns:
				if i in json:
					if len(query) == 1:
						query.append(char)
					else:
						query.append(", " + char)
					toList.append(i)
		
		dummyAdd("{}", formatting)
		query.append(") VALUES (")
		dummyAdd("%s", query)
		query.append(")")
		
		rec = Record(self.conn, sql.SQL(" ".join(query) + ";").format(tuple(formatting)), tuple(params))
		if rec.status().startswith("INSERT"):
			rec.cancel()
			return True
		rec.cancel()
		return False
	
	def removeEntry(json):
		result = Record(self.conn, sql.SQL("DELETE FROM {} WHERE id=%s;").format(sql.Identifier(json["category"])), (json["id"],))
		return True
