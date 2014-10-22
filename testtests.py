import unittest

try:
  import test as hw
except:
  pass

class SimpleTests(unittest.TestCase):

  def testA(self):
    assert hw.foo() == 42

  def testB(self):
    assert hw.bar(2) == 4


if __name__ == '__main__':
  unittest.main() #run all tests
