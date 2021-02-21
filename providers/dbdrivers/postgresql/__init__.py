#!/usr/bin/env python3
from .record import Record
from .management import Initiator
import logging, signal, psycopg2

class Driver():
	def __initDB(self):
		_CREATE
		dbhelper = Management(self.psqlconf["dbconnstr"])
		
		if self.conntries >= 2:
			logging.info("Failed to create database '{}', exiting...".format(self.psqlconf["dbname"]))
			signal.alarm(15)
			return False
		
		if not dbhelper.error == "":
			logging.info("\033[1;mDatabase does not exist\033[0;m")
			
			logging.info("creating database '{}'...".format(self.psqlconf["dbname"]))
			os.system(cmds["createdb"].format(self.psqlconf["dbname"]))
		
			logging.info("restarting...")
			self.conntries += 1
			return __initDB()
		else:
			logging.info("\033[1;mDatabase does exist\033[0;m")
		
		logging.info("checking existence of required tables...")
		for i in self.conf["tables"]:
			if dbhelper.tableExists(i):
				logging.info("\033[0;32m  '{}' exists...\033[0;m".format(i))
			else:
				logging.info("\033[0;31m  '{}' does not exist\033[0;m".format(i))
				if "table_" + i in self.conf:
					logging.info("  creating table '{}'...".format(i))
					dbhelper.executeCMD(sqls[queries[i]].format(i, ",\n".join(self.conf["table_" + i])))
				else:
					logging.info("\033[0;31mtable scheme not specified in mentorapi.yml!\033[0;m")
			
		logging.info("syncing columns (insert/remove)...")
		changes = False
		for i in self.conf["tables"]:
			if "table_" + i in self.conf:
				cols = copy.copy(self.conf["table_" + i])
				for n, content in enumerate(cols):
					colname, coltype = content.split(" ")
					cols[n] = (colname, coltype)
				changes = dbhelper.alterTable(i, cols)
	
		logging.info("generating select statement for the view creation query...")
		select = []
		select2 = []
		for i in self.conf["tables"]:
			confname = "table_" + i
			if confname in self.conf:
				for content in self.conf[confname]:
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
		self.conntries = 0
		self.psqlconf = self.conf["postgresql"]
		self.tablespecifiedby = self.conf["fieldrepresentsatable"]
		self.primaryfield = self.conf["primaryfield"]
		
		logging.info("connecting to postgresql database...")
		try:
			self.conn = psycopg2.connect(self.psqlconf["dbconnstr"])
		except psycopg2.errors.OperationalError:
			self.error = psycopg2.errors.OperationalError
		
		self.tables = {}
		for table in self.conf["tables"]:
			self.tables[table] = self.conf["table_" + table]
		
		Initiator(self.tables, self.psqlconf["dbconnstr"]).database()
		
		self.name = "PostgreSQL driver for FedGate"
		self.version = "1.0"
		self.description = "Allows the FedGate instance to use postgres as a storage engine. This will be a non-relational database"
		self.author = "Sören Reinecke alias Valor Naram"
	
#	def validateReadAction(self, func):
#		def func_wrapper(json):
#			for i in self.conf["mandatoryfields"]:
#				if not i in json: # if a mandatory field hasn't been supplied by the client, then
#					return {} # return an empty result set.
#			
#			if not self.tablespecifiedby in json: # if the table name specifier hasn't been supplied by the client, then
#				return {} # return an empty result set.
#			func(json)
#		return func_wrapper
#	
#	def validateWriteAction(self, func):
#		def dummyFunc(json):
#			return {"survivedValidator": True} # means that client's input survived the validator we call below and pass in this function
#		
#		def func_wrapper(json):
#			valInp = validateReadAction(dummyFunc) # calling 'validateReadAction' decorator and passing it a function which does nothing so our function we want to validate does not get called by the callee while we are not finish doing validation
#			result = valInp(json) # validate the 'json' python3 dictionary input using the validator 'validateReadAction'
#			
#			if not self.primaryfield in json and not len(result) == 0: # if the primary key for the primary field to send with that write request hasn't been supplied by the client and the validator we called above does not return any result, then
#				return {} # return an empty result set.
#			func(json)
#		return func_wrapper
	
	def __getEntries(self, json, query):
		table = sql.Identifier(json[self.tablespecifiedby])
		params = []
		
		del json[self.tablespecifiedby]
		
		for i in json:
			query.append(self.psqlconf["querybyfield"][i].replace("*", "%"))
			params.append(json[i])
		
		query.append("ORDER BY {} DESC LIMIT {} ".format(self.conf["orderbyfield"], self.conf["fetchrows"]))
		
		if "pagination" in json:
			query.append("OFFSET %s ROWS")
			params.append(json["pagination"]["from"])
			
			query.append("FETCH NEXT %s ROWS ONLY")
			params.append(json["pagination"]["to"])
			
			del json["pagination"]
		
		
		return sql.SQL(" ".join(query) + ";").format(table), tuple(params)
	
#	@self.validateReadAction()
	def getEntries(self, json):
		query = ["SELECT * FROM {}"]
		
		sql, param = self.__getEntries(json, query)
		return Record(self.conn, sql, param).getAll()
	
#	@self.validateReadAction()
	def getEntriesDistinct(self, json):
		query = ["SELECT DISTINCT * FROM {}"]
		
		sql, param = self.__getEntries(json, query)
		return Record(self.conn, sql, param).getAll()
	
#	@self.validateReadAction()
	def getUnique(self, json):
		query = ["SELECT DISTINCT {} FROM {}"]
		formatting = [sql.Identifier(json["column"]), json[self.tablespecifiedby]]
		param = []
		
		if "pagination" in json:
			query.append("OFFSET %s ROWS")
			params.append(json["pagination"]["from"])
			
			query.append("FETCH NEXT %s ROWS ONLY")
			params.append(json["pagination"]["to"])
		
		return Record(self.conn, sql.SQL(" ".join(query) + ";").format(tuple(formatting)), tuple(param)).getAll()
		
	
#	@self.validateWriteAction()
	def changeEntry(self, json):
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
		
		Record(self.conn, sql.SQL(" ".join(query) + ";").format(tuple(formatting)), tuple(params)).getAll()
	
#	@self.validateWriteAction()
	def addEntry(self, json):
		query = ["INSERT INTO {} ("]
		formatting = [sql.Identifier(json[self.tablespecifiedby])]
		params = []
		columns = []
		
		json[self.primaryfield] = str(uuid.uuid4())
		
		for i in self.conf["TABLE_" + json[self.tablespecifiedby]]:
			columns.append(i.split(" ", 1)[0])
		
		for i in columns:
			if i in json:
				if len(query) == 1:
					query.append("{}")
				else:
					query.append(", {}")
				formatting.append(sql.Identifier(i))
		query.append(") VALUES (")
		
		for i in columns:
			if i in json:
				if len(query) == 1:
					query.append("%s")
				else:
					query.append(", %s")
				formatting.append(i)
		
		query.append(")")
		
		rec = Record(self.conn, sql.SQL(" ".join(query) + ";").format(tuple(formatting)), tuple(params)).getAll()
		if rec.status().startswith("INSERT"):
			rec.cancel()
			return True
		rec.cancel()
		return False
	
	def removeEntry(self, json):
		result = Record(self.conn, sql.SQL("DELETE FROM {} WHERE id=%s;").format(sql.Identifier(json["category"])), (json["id"],)).getAll()
		return True
	
	def exit(self):
		logging.info("Closing connection to PostgreSQL database...")
		self.conn.close()
		return True
