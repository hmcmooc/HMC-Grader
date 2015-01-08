PLUGIN_NAME = "Supplemental File (not executed)"

def testFileParser(filename):
  return []

def runTests(cmdPrefix, testFile, timeLimit):
  summary = {}
  summary['totalTests'] = 0
  summary['failedTests'] = 0
  summary['timeout'] = timeoutReached
  summary['died'] = False
  summary['generalError'] = ""
  summary['rawOut'] = ""
  summary['rawErr'] = ""
  summary['supplemental'] = True
  return summary, {}
