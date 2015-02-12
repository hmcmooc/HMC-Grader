import unittest

import sys
import test as hw

class SimpleTests(unittest.TestCase):

  def testA(self):
    assert hw.foo() == 42

  def testB(self):
    assert hw.bar(2) == 4

  def testC(self):
    print "testC: BLAH BLAH BLAH"
    assert True

if __name__ == '__main__':
  unittest.main() #run all tests
