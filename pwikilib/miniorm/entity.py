# entity.py - entity management
#

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
	def __new__(cls, name, bases, dct):
		if bases[0] != object:
			dct['__metadata__'] = {}
			if '__table__' in dct:
				dct['__metadata__']['table'] = dct['__table__']
			else:
				dct['__metadata__']['table'] = _get_dbname(name)
		return type.__new__(cls, name, bases, dct)

class Entity(object):
	__metaclass__ = _MetaEntity

class _MetaEntityManager(type):
	def __new__(cls, name, bases, dct):
		if bases[0] != object:
			if '__entity__' not in dct:
				raise NoEntityError
		return type.__new__(cls, name, bases, dct)

class EntityManager(object):
	__metaclass__ = _MetaEntityManager

# End
