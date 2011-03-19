#
#

from pwikilib.miniorm import column
import unittest

class TestString(unittest.TestCase):
	def test_acceptString(self):
		t = column.String()
		self.assertTrue(t.accept('hello'))
		self.assertTrue(t.accept(u'hello'))
	
	def test_dataTypeIsVarchar(self):
		t = column.String()
		self.assertEqual("VARCHAR", t.get_datatype())

class TestColumn(unittest.TestCase):
	def test_setValue(self):
		c = column.Column(None)
		c.set('hello')
		self.assertEqual('hello', c.get())
	
	def test_acceptStringValue(self):
		c = column.Column(None, column.String())
		self.assertTrue(c.accept('hello'))
		self.assertFalse(c.accept(42))
	
	def test_acceptNone(self):
		c = column.Column(None, nullable=True)
		self.assertTrue(c.accept(None))
	
	def test_doesNotAcceptNone(self):
		c = column.Column(None, nullable=False)
		self.assertFalse(c.accept(None))
		
	def test_acceptNoneByDefault(self):
		c = column.Column(None)
		self.assertTrue(c.accept(None))
	
	def test_complainWhenSetByType(self):
		c = column.Column(None, column.String())
		try:
			c.set(42)
			self.fail()
		except ValueError:
			pass
	

if __name__ == '__main__':
	unittest.main()

# End
