import sys, os, stat
import re

from subprocess import Popen, PIPE

from datetime import datetime

PLUGIN_NAME = "Java (junit4)"

JAVA_TEST_REGEX = r"@Test\s+public\s+void\s+([a-zA-Z0-9-_]+)"

def testFileParser(filename):
  '''
  Takes a Java Junit test file and attempts to extract all the test names.
  '''

  with open(filename) as f:
    contents = f.read()

  testRegex = re.compile(JAVA_TEST_REGEX)

  testNames = []

  for test in testRegex.findall(contents):
    testNames.append(test)

  return testNames

def runTests(cmdPrefix, testFile, timeLimit):
  cmdCompile = ["javac", "-cp", "/usr/share/java/junit4.jar:.", testFile]
  #Not using cmdPrefix because we need to write files to the directory
  compileProc = Popen(cmdCompile, stderr=PIPE)
  _, compOut = compileProc.communicate()

  if compOut:
    #If the compiler produced output on stderr we have an issue so report it
    summary = {}
    summary['died'] = True
    summary['generalError'] = compOut
    return summary, {}

  className = testFile[:-5]
  pathName = os.getcwd()+className
  cmdRun = ["/usr/bin/java", "-cp", "/usr/share/java/junit4.jar:.", "org.junit.runner.JUnitCore", className]

  startTime = datetime.now()

  runner = Popen(cmdPrefix+cmdRun,stdout=PIPE, stderr=PIPE)

  while runner.poll() is None:
    currentTime = datetime.now()
    delta = currentTime - startTime
    if delta.total_seconds() > timeLimit:
      runner.kill()
      return {'timeout':True}, {}
      break

  stdout,stderr = runner.communicate()

  #Find all error reports
  #failedTests= re.finditer("[0-9]*\) (.+)\(\w+\)\n(?:(?:java\.lang\..+Error)|(?:org\.junit\..+Failure)): (.*)", stdout)
  testSplit = re.split(r"[0-9]*\) (.+)\(\w+\)", stdout)
  #Slice the summary off
  testSplit = testSplit[1:]

  failedTests = {}
  summary = {}
  #Parse error reports for outputting to json
  for i in range(0, len(testSplit), 2):
      # testName = fail.group(1)
      # report = {}
      # message = fail.group(2)
      # hint = message
      # expact = re.search("expected:\<(.+)\> but was:\<(.+)\>", message)
      #
      # if expact:
      #     hint = message[0:message.find("expected")-1]
      #     report['expected'] = expact.group(1)
      #     report['returned'] = expact.group(2)
      report = {}
      report['hint'] = testSplit[i+1]
      failedTests[testSplit[i]] = report

  #Creates summary info
  lastLine = re.search("OK \(([0-9]*) tests\)", stdout)
  if lastLine:
      summary['totalTests'] = int(lastLine.group(1))
      summary['failedTests'] = 0
  else:
      lastLine = re.search("FAILURES[!]+\nTests run: ([0-9]*),[ ]+Failures: ([0-9]*)", stdout)
      summary['totalTests'] = int(lastLine.group(1))
      summary['failedTests'] = int(lastLine.group(2))

  summary['timeout'] = False
  summary['died'] = False

  return summary, failedTests
