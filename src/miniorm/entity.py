# entity.py - entity management
#

import column

class NoEntityError(Exception): pass

def _get_dbname(name):
	db_name = ''
	for i in range(len(name)):
		c = name[i]
		if i > 0 and c.upper() == c:
			db_name += '_'
		db_name += c.upper()
	return db_name

class _MetaEntity(type):
	"""Meta-class for entity.
	"""
	
	def __new__(cls, name, bases, dct):
		if bases[0] != object:
			dct['__metadata__'] = {}
			metadata = dct['__metadata__']
			if '__table__' in dct:
				metadata['table'] = dct['__table__']
			else:
				metadata['table'] = _get_dbname(name)
			metadata['columns'] = []
			for name, value in dct.items():
				if isinstance(value, column.Column):
					if value.get_name() is None:
						metadata['columns'].append(_get_dbname(name))
					else:
						metadata['columns'].append(value.get_name())
		return type.__new__(cls, name, bases, dct)

class Entity(object):
	"""Entity base class.
	"""

	__metaclass__ = _MetaEntity

class _MetaEntityManager(type):
	"""Meta-class for entity manager.
	
	It checks the presence of the special class variable __entity__.  This
	variable should contain an entity class.
	"""
	
	def __new__(cls, name, bases, dct):
		if bases[0] != object:
			if '__entity__' not in dct:
				raise NoEntityError
			if not issubclass(dct['__entity__'], Entity):
				raise NoEntityError
		return type.__new__(cls, name, bases, dct)

class EntityManager(object):
	__metaclass__ = _MetaEntityManager
	
	def __init__(self, session):
		"""
		@param session: resource manager session.
		"""
		self.__session = session
	
	def get_session(self):
		return self.__session
	
	def findAll(self):
		cursor = self.__session.cursor()
		try:
			meta = self.__entity__.__metadata__
			rows = cursor.execute('SELECT ' + (', '.join(meta['columns'])) + ' FROM ' + meta['table'])
		finally:
			cursor.close()

# End
