# field.py - data field representation
#

class ColumnType(object):
	def accept(self, value):
		pass

class String(ColumnType):
	def accept(self, value):
		return isinstance(value, basestring)

class Column(object):
	def __init__(self, target, type=None, nullable=True):
		self.__target = target
		self.__type = type
		self.__nullable = nullable
		self.__value = None
	
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
