# coding=utf-8
import re, random, string
from datetime import datetime

from subprocess import Popen, PIPE

PLUGIN_NAME = "Racket (Rackunit)"

RACKET_TEST_REGEX = r"\(check-.*\?\s+\(.*\)\s+.*\s+\"([^:]+?)(?:\:.+)?\"\)"

def testFileParser(filename):
  with open(filename) as f:
    contents = f.read()

  testRegex = re.compile(RACKET_TEST_REGEX, re.M)

  testNames = []

  for test in testRegex.findall(contents):
    testNames.append(test)

  return testNames

def runTests(cmdPrefix, testFile, timeLimit):
  # Racket tests require some manipulation of the input and test files so that
  # it works nicely. We do that here
  with open(testFile, 'r') as testF:
    testText = testF.read()
    studentFileName = re.search(r'^[^;]*\(include "([^"]+)"\)',\
                                testText, re.MULTILINE).group(1)

  #Remove the #lang racket from the student file so that the import in the test
  #will work
  try:
    studentFile = open(studentFileName, 'r')
    studentFileText = studentFile.read()
    studentFile.close()

    studentFileText = re.sub(r'(#lang +racket)', r';\1\n', studentFileText)

    studentFile = open(studentFileName, 'w')
    studentFile.write(studentFileText)
    studentFile.close()
  except Exception as e:
    return {'tiemout':False, 'died':True, 'generalError': str(e)}, {}

  #Put a random string in the test file so that we can tell where the tests
  #begin.

  randline = ''.join(random.choice(string.letters + string.digits) for _ in range(10))
  testText = re.sub(r'(\(check-[^ ]+)',
                       '(displayln "' +
                        randline +
                        r'" (current-error-port))\n\1',
                        testText, count=1)

  with open(testFile, 'w') as testF:
    testF.write(testText)

  #End of manipulation of files
  #Run the tests

  startTime = datetime.now()
  testProc = Popen(cmdPrefix + ['/usr/bin/racket', testFile],\
                  stdout=PIPE, stderr=PIPE)

  while testProc.poll() is None:
    currentTime = datetime.now()
    delta = currentTime - startTime
    if delta.total_seconds() > timeLimit:
      testProc.kill()
      #Report a timeout
      return {'timeout':True, 'died':False}, {}

  testOut, testError = testProc.communicate()

  if testProc.returncode != 0:
    return {'timeout':False, 'died':True, 'generalError': testError}, {}

  try:
    testResults = testError.split(randline)[1]
  except IndexError:
    # b. If this line was never seen, then something bad happened
    return {'timeout':False, 'died':True, 'generalError': "Could not parse the test output:\n" + testOut + "\n\n" + testError}, {}
  else:
    failedTests = {}
    for failedCaseMatch in re.finditer('-'*20 + r'\n(.*?)\n' + '-'*20, testResults, flags=re.DOTALL):
      failedCase = failedCaseMatch.group(1)
      err = re.search(r'\nmessage: *"([^:]*):? *(.*)"\n', failedCase)
      if err:
        testname = err.group(1)
        msg = err.group(2)
        failedTests[testname] = {'hint': msg}

    summary = {}
    summary['died'] = False
    summary['timeout'] = False
    summary['totalTests'] = 0
    summary['failedTests'] = len(failedTests.keys())

    return summary, failedTests
