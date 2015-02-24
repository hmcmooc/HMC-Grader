# coding=utf-8

import sys
from setupDatabase import setupDatabase
from utilities import getInput, checkForProgram

#Helper function to let the user know what servers are providing what
def makeStatusMsg(mN, status):
  if status == None:
    return "Not provided"
  else:
    client = mN.getClient(status)
    return "Provided by %s:%d" % (client.listeningAddr[0], client.listeningAddr[1])



def runSetup(mN):
  print """
================================================================================
= Setup Support Services                                                       =
================================================================================

The script will now walk through setting up support services.

Which services would you like this node to provide?

  0) Database    [%s]

  1) Filesystem  [%s]

  2) Work Queue  [%s]

NOTE: This server can only provide services not provided by another server

""" % (makeStatusMsg(mN, mN.providesDB),makeStatusMsg(mN, mN.providesFS),
        makeStatusMsg(mN, mN.providesQ))

  def splitInput(input):
    return map(int, input.split(','))

  choices = getInput("What services do you want to provide? (enter a comma separated list)\n",
                    splitInput, lambda x: all(map(lambda y: y>=0 and y <=2, x)))

  print choices
  #Check if the user selected somethign that was already provided
  #If they did ask if they want to restart or if they would like to remove the
  #choice
  if 0 in choices and mN.providesDB != None:
    print """
The Database service is already being provided. If you want this server to
provide the service instead please stop the other server and restart this
script. Otherwise the script will resume without the Database option selected.
"""
    finish = getInput("Would you like to exit? [y/n] ", str, lambda x : x in ['y', 'n'])
    if finish == 'y':
      sys.exit("Terminating script")

    choices.remove(0)

  if 1 in choices and mN.providesFS != None:
    print """
The Filesystem service is already being provided. If you want this server to
provide the service instead please stop the other server and restart this
script. Otherwise the script will resume without the Filesystem option selected.
"""
    finish = getInput("Would you like to exit? [y/n] ", str, lambda x : x in ['y', 'n'])
    if finish == 'y':
      sys.exit("Terminating script")
    choices.remove(1)

  if 2 in choices and mN.providesQ != None:
    print """
The Work Queue service is already being provided. If you want this server to
provide the service instead please stop the other server and restart this
script. Otherwise the script will resume without the Work Queue option selected.
"""
    finish = getInput("Would you like to exit? [y/n] ", str, lambda x : x in ['y', 'n'])
    if finish == 'y':
      sys.exit("Terminating script")

    choices.remove(2)

  #If all the choices got removed we terminate here
  if choices == []:
    sys.exit("All services provided by other systems. Terminating script")

  #Here we set up the various services
  if 0 in choices:
    setupDatabase(mN)

  if 1 in choices:
    setupFilesystem(mN)

  if 2 in choices:
    setupWorkQueue(mN)

  return None


def setupFilesystem(mN):
  mN.providesFS = -1
  pass

def setupWorkQueue(mN):
  mN.providesQ = -1
  pass
