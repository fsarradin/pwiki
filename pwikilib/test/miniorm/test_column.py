##from pwikilib.miniorm import columnimport unittestclass TestColumn(unittest.TestCase):	def test_setValue(self):		c = column.Column(None, None)		c.set('hello')		self.assertEqual('hello', c.get())if __name__ == '__main__':	unittest.main()# End