# field.py - data field representation
#

class ColumnType(object):
	def accept(self, value):
		pass
	
	def get_datatype():
		pass

class String(ColumnType):
	def accept(self, value):
		return isinstance(value, basestring)

	def get_datatype():
		return "VARCHAR"

class Column(object):
	def __init__(self, name=None, type=None, nullable=True):
		self.__name = name
		self.__type = type
		self.__nullable = nullable
		self.__value = None
	
	def get_name(self):
		return self.__name
	
	def is_nullable(self):
		return self.__nullable
	
	def get_type(self):
		return self.__type
	
	def get(self):
		return self.__value
	
	def accept(self, value):
		if value is None:
			return self.__nullable
		if self.__type is not None:
			return self.__type.accept(value)
		return True
	
	def set(self, value):
		if self.accept(value):
			self.__value = value
		else:
			raise ValueError

# End
