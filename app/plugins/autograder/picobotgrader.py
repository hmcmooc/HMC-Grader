import re
from datetime import datetime
from random import randint

PLUGIN_NAME = "Picobot"
PICO_REGEX = r"^(.*):\s*((\d+)\s*,\s*(\d+)|random)$"

def testFileParser(filename):
  with open(filename) as f:
    contents = f.read()

  testRegex = re.compile(PICO_REGEX, re.M)
  testNames = []
  for testMatch in testRegex.finditer(contents):
    testNames.append(testMatch.group(1))
  return testNames

def runTests(cmdPrefix, testFile, timeLimit):
  with open(testFile) as f:
    mapName = f.readline()[:-1]
    studentFile = f.readline()[:-1]
    f.readline()
    tests = f.read()

  testRegex = re.compile(PICO_REGEX, re.M)

  summary = {}
  summary['totalTests'] = 0
  summary['failedTests'] = 0
  summary['rawOut'] = ""
  summary['rawErr'] = ""
  summary['died'] = False
  summary['timeout'] = False

  failedTests = {}
  for testMatch in testRegex.finditer(tests):
    summary['totalTests'] += 1
    if testMatch.group(2) == "random":
      p = Picobot(mapName)
    else:
      x = int(testMatch.group(3))
      y = int(testMatch.group(4))
      p = Picobot(mapName, x, y)

    summary['rawOut'] += "%s: Picobot started at (%d,%d)\n" % (testMatch.group(1), p.pos[0], p.pos[1])
    success, msg = p.loadRules(studentFile)

    if not success:
      summary['failedTests'] += 1
      failedTests[testMatch.group(1)] = {'hint': msg}
      continue

    stepFailed = False
    for step in range(MAX_STEPS):
      success, msg = p.step()

      if not success:
        summary['failedTests'] += 1
        failedTests[testMatch.group(1)] = {'hint': msg}
        stepFailed = True
        break

      if p.countUnvisited() == 0:
        break

    if stepFailed:
      continue

    if p.countUnvisited() > 0:
      summary['failedTests'] += 1
      failedTests[testMatch.group(1)] = {'hint': "Didn't fill all squares in %d steps" % (MAX_STEPS)}
      continue


  return summary, failedTests

#
# The picobot simulator
#

MAX_STEPS = 5000
RULE_REGEX = r"(\d+)\s+([NEWSnewsxX\*]{4})\s+->\s+([NEWSnewsXx])\s+(\d+)"
COMMENT_REGEX = r"^#.*$"
BLANK_REGEX = r"^\s*$"

def validRule(rule, surroundings):
  for index, letter in enumerate(rule[1]):
    if letter == "*":
      continue
    elif letter != surroundings[index]:
      return False
  return True

def parseRules(filename):
  rules = []
  with open(filename) as f:
    for line in f:
      m = re.match(RULE_REGEX, line)
      if m:
        rules.append((int(m.group(1)), m.group(2).upper(), m.group(3).upper(), int(m.group(4))))
        continue
      m = re.match(COMMENT_REGEX, line)
      if m:
        continue
      m = re.match(BLANK_REGEX, line)
      if not m:
        #Then we have a non rule and non-comment so parse error
        print line
        return rules, False

  return rules, True

class Picobot(object):
  def __init__(self, mapName, x=-1, y=-1):
    self.state = 0
    self.rules = []
    self.map = MAPS[mapName]

    if x == -1 or y == -1:
      x, y = (0,0)
      while self.map[x][y] != 0:
        x = randint(0, len(self.map[0])-1)
        y = randint(0, len(self.map)-1)

    self.pos = [x,y]

    self.map[x][y] = 2

  def loadRules(self, ruleFile):
    self.rules, success = parseRules(ruleFile)
    if success:
      return True, ""
    else:
      return False, "Rule file contains invalid picbot rule"

  def step(self):
    surroundings = self.getSurroundings()

    validRules = [x for x in self.rules if x[0] == self.state and validRule(x, surroundings)]

    if len(validRules) == 0:
      return False, "No valid rule for state (%d, %s)" % (self.state, surroundings)

    if len(validRules) > 1:
      return False, "Multiple rules found for state (%d, %s):\n%s" %(self.state, surroundings, str(validRules))

    rule = validRules[0]

    if rule[2] == "N":
      self.pos[0] -= 1

    if rule[2] == "E":
      self.pos[1] += 1

    if rule[2] == "W":
      self.pos[1] -= 1

    if rule[2] == "S":
      self.pos[0] += 1

    if self.map[self.pos[0]][self.pos[1]] == 1:
      return False, "Rule caused picobot to run into a wall"

    self.map[self.pos[0]][self.pos[1]] = 2

    self.state = rule[3]

    return True, ""

  def countUnvisited(self):
    unvisited = 0
    for row in self.map:
      for col in row:
        if col == 0:
          unvisited += 1
    return unvisited


  def getSurroundings(self):
    out = ""
    if self.map[self.pos[0]-1][self.pos[1]] == 1:
      out += "N"
    else:
      out += "X"

    if self.map[self.pos[0]][self.pos[1]+1] == 1:
      out += "E"
    else:
      out += "X"

    if self.map[self.pos[0]][self.pos[1]-1] == 1:
      out += "W"
    else:
      out += "X"

    if self.map[self.pos[0]+1][self.pos[1]] == 1:
      out += "S"
    else:
      out += "X"

    return out
#
# MAPS
#

EMPTY_MAP = \
  [
   [ 1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1 ] ]

MAZE_MAP = \
  [
   [ 1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1 ],
   [ 1,0,0,1,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,1,0,1 ],
   [ 1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,0,1,0,0,0,0,1 ],
   [ 1,1,0,1,0,1,1,1,0,1,0,1,0,1,0,1,1,1,1,1,1,1,1,0,1 ],
   [ 1,0,0,1,0,0,0,0,0,1,0,1,0,1,0,0,0,1,0,0,0,0,1,0,1 ],
   [ 1,0,1,1,1,0,1,1,1,1,0,1,0,1,0,1,0,1,0,1,1,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1,1,1,1,1,1 ],
   [ 1,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,0,1,0,0,1,0,0,0,1 ],
   [ 1,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,1,1,0,1,0,1,1,1 ],
   [ 1,1,0,1,0,1,0,0,0,1,0,1,0,1,1,1,0,0,1,0,1,0,0,0,1 ],
   [ 1,1,0,1,0,1,1,1,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1 ],
   [ 1,1,0,1,0,0,0,0,0,1,0,0,0,1,0,0,0,0,1,0,1,1,1,0,1 ],
   [ 1,1,0,1,1,1,1,1,0,1,1,0,1,1,1,1,1,0,1,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,1,0,1,1,0,0,0,0,0,1,0,1,1,1,0,1,0,1 ],
   [ 1,0,1,1,1,1,1,1,0,1,0,0,1,1,1,0,1,0,0,0,1,0,1,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,1,0,1,1,0,1,0,1,1,1,0,1,0,1,0,1 ],
   [ 1,1,1,1,1,1,1,1,1,1,0,1,0,0,1,0,0,0,1,0,1,0,1,0,1 ],
   [ 1,0,0,0,0,1,0,0,0,1,1,1,0,1,1,1,1,0,1,0,1,0,1,0,1 ],
   [ 1,0,1,1,0,1,0,1,0,0,0,0,0,0,0,0,1,0,1,0,1,1,1,0,1 ],
   [ 1,0,0,1,0,1,0,1,1,1,1,1,0,1,1,0,1,0,1,0,1,0,1,0,1 ],
   [ 1,0,1,1,0,1,0,1,0,1,0,0,0,1,0,0,1,0,0,0,1,0,0,0,1 ],
   [ 1,0,1,0,0,1,0,1,0,0,0,1,1,1,0,1,1,1,1,1,1,1,0,1,1 ],
   [ 1,0,1,1,1,1,0,1,0,1,0,0,0,1,0,1,0,0,0,0,0,1,0,1,1 ],
   [ 1,0,0,0,0,0,0,1,0,1,1,1,0,1,0,0,0,1,1,1,0,0,0,1,1 ],
   [ 1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1 ] ]

EXTRA_MAP = \
  [
   [ 1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1 ],
   [ 1,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,1,1,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,1,1,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,1,1,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1 ],
   [ 1,0,0,0,1,1,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1 ],
   [ 1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1 ],
   [ 1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1 ],
   [ 1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1 ],
   [ 1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,1 ],
   [ 1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1 ],
   [ 1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1 ],
   [ 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1 ],
   [ 1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1 ] ]

MAPS = {'emptyMap': EMPTY_MAP,
'mazeMap': MAZE_MAP,
'extraMap': EXTRA_MAP}
