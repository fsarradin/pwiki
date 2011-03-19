#
#

from pwikilib.miniorm import entity
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
	def test_shouldHaveBoundEntity(self):
		class E(entity.Entity): pass
		class EM(entity.EntityManager):
			__entity__ = E

	def test_complainWhenNoBoundEntity(self):
		try:
			class EM(entity.EntityManager):
				pass
			self.fail("An exception should be raised when no entity is bound to the manager")
		except entity.NoEntityError:
			pass

if __name__ == '__main__':
	unittest.main()

# End
