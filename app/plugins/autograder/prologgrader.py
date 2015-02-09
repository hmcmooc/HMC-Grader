import re
from datetime import datetime
from subprocess import Popen, PIPE

from app.helpers.command import Command

PLUGIN_NAME = "Prolog (plunit)"

PROLOG_TEST_REGEX = r"^test\((.*)\) *:- .*$"

def testFileParser(filename):
  '''Takes a prolog test file and attempts to extract all the tests'''
  with open(filename) as f:
    contents = f.read()

  testRegex = re.compile(PROLOG_TEST_REGEX, re.M)

  testNames = []
  for test in testRegex.findall(contents):
    testNames.append(test)

  return testNames


def runTests(cmdPrefix, testFile, timeLimit):
  startTime = datetime.now()
  # testProc = Popen(cmdPrefix + ['swipl', '-s', testFile, '-g', 'run_tests', '-t', 'halt'], stdout=PIPE, stderr=PIPE)
  #
  # timeoutReached = False
  # while testProc.poll() is None:
  #   currentTime = datetime.now()
  #   delta = currentTime - startTime
  #   if delta.total_seconds() > timeLimit:
  #     testProc.kill()
  #     timeoutReached = True
  #     break

  testProc = Command(cmdPrefix + ['swipl', '-s', testFile, '-g', 'run_tests', '-t', 'halt'])

  timeoutReached, testOut, testError = testProc.run(timeout=int(timeLimit), env=environ)

  if timeoutReached:
    summary = {}
    summary['totalTests'] = 0
    summary['failedTests'] = 0
    summary['timeout'] = timeoutReached
    summary['died'] = False
    summary['generalError'] = ""
    summary['rawOut'] = ""
    summary['rawErr'] = ""

    return summary, {}

  #testOut, testError = testProc.communicate()

  summary = {}
  summary['rawOut'] = testOut
  summary['rawErr'] = testError
  summary['timeout'] = False

  testOut = testError.split('\n')
  failedTests = {}
  for line in testOut:
    if re.match(r"^% No tests to run$", line):
      #Compilation error
      summary['died'] = True
      summary['totalTests'] = 0
      summary['failedTests'] = 0

    if re.match("\ttest \w*: [(failed)(received error)]", line):
      failedTests[line[6:line.find(":")]] = {'hint':""}

  summary['totalTests'] = "N/A"
  summary['failedTests'] = "N/A"
  summary['died'] = False

  return summary, failedTests
