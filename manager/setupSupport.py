# coding=utf-8

import sys
from utilities import getInput, checkForProgram, makeStatusMsg, getYN
from manageNode import ManageNode


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

  print """
================================================================================
= Beginning service data gathering                                             =
================================================================================

Currently this script does not support configuring the neede systems for use
with the CS> system. Instead it is simply here to help configure and maintain
the system.

With this in mind prior to continuing setup please make sure you have followed
the instructions here:

https://github.com/robojeb/HMC-Grader/wiki/Setup-HMC-Grader#setup-steps

to set up the appropriate services this server will provide. When setup
continues the system will ask you for information you created during setup

NOTE: The system assumes that all the services are capable of listening on the
IP address which was selected earlier.
"""
  choice = getYN("Are you ready to continue? [y/n] ")

  if choice == 'n':
    sys.exit("Script terminating")

  #Here we set up the various services
  if 0 in choices:
    setupDatabase(mN)

  if 1 in choices:
    setupFilesystem(mN)

  if 2 in choices:
    setupWorkQueue(mN)

  for client in mN.clients.values():
    if 0 in choices:
      client.sendMsg(ManageNode.PROVIDES_MSG, 'DB')
    if 1 in choices:
      client.sendMsg(ManageNode.PROVIDES_MSG, 'FS')
    if 2 in choices:
      client.sendMsg(ManageNode.PROVIDES_MSG, 'Q')
  pass


def setupDatabase(mN):
  print """
================================================================================
= Database Service: Gathering Information                                      =
================================================================================
"""
  mN.dbInfo = {}

  def checkIP(ip):
    import re
    if re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', ip):
      return True
    else:
      return False

  mN.dbInfo['dbPort'] = getInput("What port is the database listening on?: ", int, lambda x: True)
  mN.dbInfo['dbName'] = getInput("What is the name of the database?: ", str, lambda x: True)
  mN.dbInfo['dbUser'] = getInput("What is the name of the database user?:", str, lambda x: True)
  print "What is the database user password?"
  mN.dbInfo['dbPass'] = getpass()
  mN.providesDB = -1
  print """
================================================================================
= Database Service: Configured                                                 =
================================================================================
"""


def setupFilesystem(mN):
  print """
================================================================================
= File System Service: Gathering Information                                   =
================================================================================
"""
  filePath = getInput("Where do you want to store the data? (Absolute path): ", str, lambda x: True)
  print "Setting up storage space..."
  def ensurePathExists(path):
    import os
    if not os.path.isdir(path):
      os.makedirs(path)

  from os.path import join
  ensurePathExists(filePath)
  ensurePathExists(join(filePath, 'submissions'))
  ensurePathExists(join(filePath, 'plugins/autograder'))
  ensurePathExists(join(filePath, 'plugins/latework'))
  print "Storage space setup complete."
  user = getInput("What user should other nodes connect as?: ", str, lambda x: True)
  ensurePathExists(keyPath)
  mN.fsInfo = {}
  mN.fsInfo['filePath'] = filePath
  mN.fsInfo['user'] = user
  mN.providesFS = -1
  print """
================================================================================
= File System Service: Configured                                              =
================================================================================
"""

def setupWorkQueue(mN):
  print """
================================================================================
= Work Queue Service: Gathering Information                                    =
================================================================================
"""
  def checkIP(ip):
    import re
    if re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', ip):
      return True
    else:
      return False
  mN.qInfo = {}
  mN.qInfo['qUser'] = getInput("What is the name of the work queue user?:", str, lambda x: True)
  print "What is the work queue password?"
  mN.qInfo['qPass'] = getpass()
  mN.providesQ = -1
  print """
================================================================================
= Work Queue Service: Configured                                               =
================================================================================
"""
