#!/usr/bin/env python3

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
