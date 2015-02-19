# coding=utf-8

import pexpect
from utilities import checkForProgram, getInput, getYN

def setupDatabase(mN):
  print """
================================================================================
= Setting up database services                                                 =
================================================================================
"""

  #Check for the software we have to install
  #For the database there is only 1 now but the future might need more
  softwareToInstall = []
  if not checkForProgram("mongo"):
    softwareToInstall.append("mongo")

  if not softwareToInstall == []:
    print "Setup needs to install the following program(s) to continue:"
    for s in softwareToInstall:
      print "  * %s" % s

    install = getYN("Allow install? [y/n] ")

    if not install:
      sys.exit("Couln't install required programs aborting.")

    if 'mongo' in softwareToInstall:
      installMongo()

    #If mongo has just been installed we must be setting up a new database
    setupNewDatabase()
  else:
    print "Required programs already installed\n"
    #We don't know how much of the database is set up so we ask lots of
    #questions
    setupExistingDatabase()

  print """
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
+ Database service setup successful                                            +
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
"""

def installMongo():
  print "Now installing MongoDB 2.6.7"
  #Following mongo installation instructions from
  #https://pexpect.readthedocs.org/en/latest/api/pexpect.html
  pexpect.run("apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10")
  pexpect.run("echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' | sudo tee /etc/apt/sources.list.d/mongodb.list")
  pexpect.run("apt-get update")
  #We install this version because we know this on works (it has been tested)
  pexpect.run("apt-get install -y mongodb-org=2.6.7")
  #Start the mongo service
  pexpect.run("service mongod start")
  print "MongoDB installed"

def setupNewDatabase():
  #connect to the database
  mongo = pexpect.spawn("mongo")
  mongo.expect(".*>.*")
  pass

def setupExistingDatabase():
  pass
