from app import app
from os import listdir, getcwd
from os.path import isfile, join, basename, dirname, splitext
import imp

def getTestFileParsers():
  files = [f for f in listdir(dirname(__file__)) if isfile(join(dirname(__file__), f)) and splitext(f)[1] == ".py"]
  searchList = [dirname(__file__)]
  if app.config['AUTOGRADER_PLUGIN_PATH'] != None:
    files += [f for f in listdir(app.config['AUTOGRADER_PLUGIN_PATH']) if isfile(join(app.config['AUTOGRADER_PLUGIN_PATH'], f)) and splitext(f)[1] == ".py"]
    searchList.append(app.config['AUTOGRADER_PLUGIN_PATH'])
  out = {}
  for f in files:
      if f == "__init__.py":
          continue
      name = f.split('.')[0]
      moduleInfo = imp.find_module(name, searchList)
      m = imp.load_module(name, moduleInfo[0], moduleInfo[1], moduleInfo[2])
      out[m.PLUGIN_NAME] = m.testFileParser
  return out

def getTestResultParsers():
  files = [f for f in listdir(dirname(__file__)) if isfile(join(dirname(__file__), f)) and splitext(f)[1] == ".py"]
  searchList = [dirname(__file__)]
  if app.config['AUTOGRADER_PLUGIN_PATH'] != None:
    files += [f for f in listdir(app.config['AUTOGRADER_PLUGIN_PATH']) if isfile(join(app.config['AUTOGRADER_PLUGIN_PATH'], f)) and splitext(f)[1] == ".py"]
    searchList.append(app.config['AUTOGRADER_PLUGIN_PATH'])
  out = {}
  for f in files:
      if f == "__init__.py":
          continue
      name = f.split('.')[0]
      moduleInfo = imp.find_module(name, searchList)
      m = imp.load_module(name, moduleInfo[0], moduleInfo[1], moduleInfo[2])
      out[m.PLUGIN_NAME] = m.testResultParser
  return out


def getTestRunners():
  files = [f for f in listdir(dirname(__file__)) if isfile(join(dirname(__file__), f)) and splitext(f)[1] == ".py"]
  searchList = [dirname(__file__)]
  if app.config['AUTOGRADER_PLUGIN_PATH'] != None:
    files += [f for f in listdir(app.config['AUTOGRADER_PLUGIN_PATH']) if isfile(join(app.config['AUTOGRADER_PLUGIN_PATH'], f)) and splitext(f)[1] == ".py"]
    searchList.append(app.config['AUTOGRADER_PLUGIN_PATH'])
  out = {}
  for f in files:
      if f == "__init__.py":
          continue
      name = f.split('.')[0]
      moduleInfo = imp.find_module(name, searchList)
      m = imp.load_module(name, moduleInfo[0], moduleInfo[1], moduleInfo[2])
      out[m.PLUGIN_NAME] = m.runTests
  return out
