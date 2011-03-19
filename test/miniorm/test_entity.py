#
#

from pwikilib.miniorm import entity, column
import unittest

class TestEntity(unittest.TestCase):
	def test_mayHaveExplicitBoundedTable(self):
		class E(entity.Entity): __table__ = 'TABLE'
		self.assertEqual('TABLE', E.__metadata__['table'])

	def test_mayHaveNoExplicitBoundedTable(self):
		class E(entity.Entity): pass
		self.assertEqual('E', E.__metadata__['table'])
	
	def test_shouldTranslateCamelCase(self):
		class MyEntity(entity.Entity): pass
		self.assertEqual('MY_ENTITY', MyEntity.__metadata__['table'])

class TestEntityManager(unittest.TestCase):
	def test_shouldBeBoundToEntity(self):
		class E(entity.Entity): pass
		class EM(entity.EntityManager):
			__entity__ = E

	def test_shouldComplainIfNotBoundToEntity(self):
		class WhatEver(object): pass
		try:
			class EM(entity.EntityManager):
				__entity__ = WhatEver
			self.fail("An exception should be raised when no entity is bound to the manager")
		except entity.NoEntityError:
			pass

	def test_complainWhenNoBoundEntity(self):
		try:
			class EM(entity.EntityManager):
				pass
			self.fail("An exception should be raised when no entity is bound to the manager")
		except entity.NoEntityError:
			pass

class DummyCursor(object):
	def __init__(self):
		self.__executed = []

	def execute(self, query, *args):
		self.__executed.append((query, args))
	
	def close(self):
		pass
	
	def get_executed(self):
		return self.__executed

class DummyConnection(object):
	def __init__(self):
		self.__created_cursors = []
	
	def cursor(self):
		cursor = DummyCursor()
		self.__created_cursors.append(cursor)
		return cursor
	
	def close(self):
		pass
	
	def get_created_cursors(self):
		return self.__created_cursors

class DummyEntity(entity.Entity):
	__table__ = 'DUMMY_TABLE'
	
	id = column.Column('ROW_ID')
	value = column.Column()

class DummyEntityManager(entity.EntityManager):
	__entity__ = DummyEntity
	
	def __init__(self, session):
		entity.EntityManager.__init__(self, session)

class TestEntity_Extended(unittest.TestCase):
	def setUp(self):
		self.entity = DummyEntity()
	
	def test_shouldHaveTableName(self):
		self.assertEqual('DUMMY_TABLE', self.entity.__metadata__['table'])
	
	def test_shouldHaveColumns(self):
		columns = self.entity.__metadata__['columns']
		self.assertEqual(2, len(columns))
		self.assertTrue('ROW_ID' in columns)
		self.assertTrue('VALUE' in columns)

class TestEntityManager_Extended(unittest.TestCase):
	def setUp(self):
		self.connection = DummyConnection()
		self.manager = DummyEntityManager(self.connection)
	
	def test_findAllEntity(self):
		self.manager.findAll()
		
		cursors = self.connection.get_created_cursors()
		query, args = cursors[0].get_executed()[0]
		self.assertTrue(query == 'SELECT ROW_ID, VALUE FROM DUMMY_TABLE'
			or query == 'SELECT VALUE, ROW_ID FROM DUMMY_TABLE')

if __name__ == '__main__':
	unittest.main()

# End
