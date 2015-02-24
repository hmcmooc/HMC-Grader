# coding=utf-8
import pexpect

def checkForProgram(program):
  return len(pexpect.run("which " +program)) > 0

def getInput(msg, typecast, verify, tryLimit=5):
  tries = 0
  while tries < tryLimit:
    try:
      data = typecast(raw_input(msg))
      if not verify(data):
        tries += 1
        print "Invalid input please try again\n"
        continue
      else:
        return data
    except ValueError:
      print "Data couldn't be converted to correct type. Please try again\n"
      tries += 1
      continue

  sys.exit("Maximum number of tries exceeded exiting program")

def getYN(msg):
  return getInput(msg, str, lambda x: x in ['y','n']) == 'y'

def makeStatusMsg(mN, status):
  if status == None:
    return "Not provided"
  else:
    client = mN.getClient(status)
    return "Provided by %s:%d" % (client.listeningAddr[0], client.listeningAddr[1])
