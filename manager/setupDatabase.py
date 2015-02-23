# coding=utf-8

import pexpect, sys, re
from getpass import getpass
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
    setupNewDatabase(mN)
  else:
    print "Required programs already installed\n"
    #We don't know how much of the database is set up so we ask lots of
    #questions
    setupExistingDatabase(mN)

  print """
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
+ Database service setup successful                                            +
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
"""

def installMongo():
  print """
Now installing MongoDB 2.6.7...

This could take some time. Get up and stretch we will be here when you get back.
"""
  #Following mongo installation instructions from
  #https://pexpect.readthedocs.org/en/latest/api/pexpect.html
  pexpect.run("apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10")
  with open('/etc/apt/sources.list.d/mongodb.list', 'w') as f:
    f.write('deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen')
  #pexpect.run("echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' | sudo tee /etc/apt/sources.list.d/mongodb.list")
  pexpect.run("apt-get update")
  #We install this version because we know this on works (it has been tested)
  pexpect.run("apt-get install -y mongodb-org=2.6.7")
  #Start the mongo service
  pexpect.run("service mongod start")
  print "MongoDB installed"

def setupNewDatabase(mN):
  print """
Begining configuration for new database
"""
  #connect to the database
  mongo = pexpect.spawn("mongo")
  mongo.expect("> ")
  mongo.sendline("use admin")
  mongo.expect("switched to db admin\n> ")
  #Try to get a password for the admin user.
  while True:
    print "Enter password for administrator account: "
    password = getPass()
    print "Confirm password: "
    passConfirm = getPass()

    if password == passConfirm:
      break

    print "Passwords didn't match...\n"

  mongo.sendline('db.createUser({user: "siteUserAdmin",pwd: "%s",roles: [ { role: "userAdminAnyDatabase", db: "admin" } ]})' %password)
  mongo.sendline("quit()")
  print """
Created administrator account: siteUserAdmin

If setup should fail from this point on you can resume from step 5.iii in the
instructions at the following URL:

https://github.com/robojeb/HMC-Grader/wiki/Setup-HMC-Grader

Now editing mongo.conf file to enable authentication...
"""
  #Open the config file
  with open('/etc/mongodb.conf', 'r') as confFile:
    conf = confFIle.read()

  #Replace 2 lines
  #comment out the bind_ip line
  conf = re.sub('bind_ip', '#bind_ip', conf)
  #uncomment the auth line
  conf = re.sub('#auth', 'auth', conf)

  #Write out the new file
  with open('/etc/mongodb.conf', 'r') as confFile:
    confFile.write(conf)

  pexpect.run("service mongod restart")
  print """
Configuration file modified restarted mongod
"""

  mongo = pexpect.spawn("mongo -u siteUserAdmin -p --authenticationDatabase admin")
  mongo.expect("Enter password: ")
  mongo.sendLine(password)
  mongo.expect("> ")

  dbName = getInput("Enter a name for the database (all lowercase no spaces): ", str, lambda x: True)
  dbName = dbName.lower()
  dbName = re.sub('\w','', dbName)

  print """
Creating database:  %s
""" % (dbName)

  mongo.sendline("use %s"%(dbName))

  dbUser = getInput("Enter a username for the submission site database: ", str, lambda x: True)
  dbUser = dbUser.lower()
  dbUser = re.sub('\w','', dbUser)

  print """
Creating user: %s
""" % (dbUser)

  #Try to get a password for the admin user.
  while True:
    print "Enter password for database account: "
    userPassword = getPass()
    print "Confirm password: "
    passConfirm = getPass()

    if userPassword == passConfirm:
      break

    print "Passwords didn't match...\n"

  mongo.sendline('db.createUser({ user: "%s", pwd:"%s", roles:[{role:"dbOwner", db:"submissionSite"}]})')
  print """
Created the user account
"""
  mongo.sendline("quit()")

  mN.dbInfo = {}
  mN.dbInfo['dbUser'] = dbUser
  mN.dbInfo['dbPass'] = userPassword
  mN.dbInfo['dbPort'] = 27017
  mN.dbInfo['dbName'] = dbName


def setupExistingDatabase(mN):
  pass
