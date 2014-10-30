import re
from subprocess import Popen, PIPE
from os import environ

import itertools, json

PLUGIN_NAME = "Python"

PYTHON_TEST_REGEX=r"^.*?def (.*?)\(self\):$"

def testFileParser(filename):
  '''
  Takes a python pyunit test file and attempts to extract all the tests.
  It may accidentally grab other helper functions you define because it is
  using a simple regex search.
  '''
  with open(filename) as f:
    contents = f.read()

  testRegex = re.compile(PYTHON_TEST_REGEX, re.M)

  testNames = []

  for test in testRegex.findall(contents):
    if test != "setUp" and test != "tearDown":
      testNames.append(test)

  return testNames

def runTests():
  return ""

def testResultParser(output, error):
  failedSections = error.split('='*70)

  splitList = []
  for section in failedSections:
    splitList.append(section.split('-'*70))

  #Flatten the list
  sections = list(itertools.chain.from_iterable(splitList))

  #Check how many tests were run based on the summary
  summarySection = sections[-1]
  summaryWords = summarySection.split()

  summary = {}
  summary['total'] = int(summaryWords[1])

  failedSections = sections[1:-1]
  summary['failed'] = int(len(failedSections)/2)
  summary['died'] = False

  failedTests = {}

  #Extract the messages for the failed tests
  for i in range(0, len(failedSections), 2):
    header = failedSections[i]
    headerParts = header.split()
    tname = headerParts[1]

    pyunitmsg = failedSections[i+1]

    failedTests[tname] = {'hint': pyunitmsg}

  return summary, failedTests
