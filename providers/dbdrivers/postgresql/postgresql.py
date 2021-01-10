#!/usr/bin/env python3
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extensions import ISOLATION_LEVEL_DEFAULT
from psycopg2 import sql
from management import Initiator
import psycopg2, uuid, logging, signal

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

class Driver():
	def __init__(self, conf):
		self.conf = conf
		self.tables = {}
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
		self.description = "Allows the FedGate instance to use postgres as a storage engine. This will be a non-relational database"
		self.author = "Sören Reinecke alias Valor Naram"
		
		for table in self.conf["tables"]:
			self.tables[table] = self.conf["table_" + table]
		
		self.DBInitiator = Initiator(self.tables, self.psqlconf["dbconnstr"])
		
		logging.info("Initiating database...")
		self.DBInitiator.database()
	
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
	
	def getEntries(self, json):
		query = ["SELECT * FROM {}"]
		
		sql, param = self.__getEntries(json, query)
		return Record(self.conn, sql, param).get()
	
	def getEntriesDistinct(self, json):
		query = ["SELECT DISTINCT * FROM {}"]
		
		sql, param = self.__getEntries(json, query)
		return Record(self.conn, sql, param).get()
	
	def getUnique(self, json):
		query = ["SELECT DISTINCT {} FROM {}"]
		formatting = [sql.Identifier(json["column"]), json[self.tablespecifiedby]]
		param = []
		
		if "pagination" in json:
			query.append("OFFSET %s ROWS")
			params.append(json["pagination"]["from"])
			
			query.append("FETCH NEXT %s ROWS ONLY")
			params.append(json["pagination"]["to"])
		
		return Record(self.conn, sql.SQL(" ".join(query) + ";").format(tuple(formatting)), tuple(param))
	
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
		
		Record(self.conn, sql.SQL(" ".join(query) + ";").format(tuple(formatting)), tuple(params)).get()
	
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
		
		rec = Record(self.conn, sql.SQL(" ".join(query) + ";").format(tuple(formatting)), tuple(params))
		if rec.status().startswith("INSERT"):
			rec.cancel()
			return True
		rec.cancel()
		return False
	
	def removeEntry(self, json):
		result = Record(self.conn, sql.SQL("DELETE FROM {} WHERE id=%s;").format(sql.Identifier(json["category"])), (json["id"],))
		return True
	
	def exit(self):
		logging.info("Closing connection to PostgreSQL database...")
		self.conn.close()
		return True
