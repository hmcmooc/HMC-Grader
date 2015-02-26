#!/usr/bin/python
# coding=utf-8

"""
This script helps setup and manage a node in the CS> system.

This file is pretty large and has a lot of weird formatting for output purposes
but if you read it it should be pretty self explanatory.
"""

import os, sys, time, socket
import netifaces, pexpect

from manager import setupSupport, setupApplication
from manager.manageNode import ManageNode
from manager.manageConsole import commandLine
from manager.utilities import getInput

def getListeningIP():
  print """
This machine can listen on the following addresses
"""
  iplist = []
  ipnum = 0
  for interface in netifaces.interfaces():
        for link in netifaces.ifaddresses(interface)[netifaces.AF_INET]:
          print " %d) %s" % (ipnum, link['addr'])
          iplist.append(link['addr'])
          ipnum += 1
        for link in netifaces.ifaddresses(interface)[netifaces.AF_INET6]:
          print " %d) %s" % (ipnum, link['addr'])
          iplist.append(link['addr'])
          ipnum += 1

  choice = getInput("Use address #: ", int, lambda x: x >=0 and x < ipnum)

  return iplist[choice]



if __name__ == "__main__":
  if not os.geteuid() == 0:
    sys.exit('Script must be run as root')

  print """
================================================================================
= WARNING                                                                      =
================================================================================

This program is intended to stay running to allow for easy management of the
CS> system. It is reccomended that it be run inside a screen session so that
it can be detached and re attached later. Alternatively you can send it to the
background when the interactive portion is over.

Press enter to continue...
"""

  #Wait for user to continue
  sys.stdin.readline()

  print """
================================================================================
= Welcome!                                                                     =
================================================================================

This script will walk you through setting up a server for the CS> submission
system.

NOTE:
You must first set up the support servers before launching any of the
application servers.

ABOUT PERMISSIONS:
This script is running as a root user. Do NOT fear. The script will drop
permissions as needed to prevent web-servers and auto-graders from running with
root permissions.

Press enter to continue...
"""

  #Wait for user to continue
  sys.stdin.readline()

  #We ask the user what type of server they want to launch
  print """
================================================================================
= Choose server type                                                           =
================================================================================

Is this server going to be a support or application server?

0) Support server (Database, Filesystem, and/or Queue services)

1) Application server (Gunicorn+nginx and/or Celery worker)

NOTE: If you want both the support and the application server on this machine
you can simply run this script twice.


"""

  #Get their choice
  choice = getInput("Enter choice: ", int, lambda x: x==0 or x==1)

  print """
================================================================================
= Set manager listening port                                                   =
================================================================================

This script will set up a thread that listens for commands from the
applicationManager.py script.

By default this script will use port 9050.
If that port is already in use (eg. from another instance of this scrip running
on this server) please provide a port number now.

"""
  #A small function to check if the input is either all digits or is empty
  def checkPort(port):
    import re
    if re.match(r'^$|\d+', port):
      return True
    else:
      return False

  ip = getListeningIP()

  port = getInput("Enter port number (Default 9050): ", str, checkPort)

  #If the port is empty set it to the default otherwise use the port
  if port == '':
    port = 9050
  else:
    port = int(port)

  #Spawn the node object
  mN = ManageNode(ip, port)
  mN.start()

  #Now that we have started the node we want to make sure that if anything
  #crashes we stop and join the node thread. To do this we utilize a try-finally
  #block
  try:
    print """
================================================================================
= Connect to the management netowork                                           =
================================================================================

This script utilizes a distributed managment system for diagnostics and ease of
use. By connecting to the managment network many parts of the setup will be
automatic.

"""

    firstNode = getInput("Is this the first node [y/n]?: ", str, lambda x: x in ['y', 'n'])

    #The only restriction is that the first node cannot be an application node
    if firstNode == 'y' and choice == 1:
      sys.exit("""
The first node in the system cannot be an application node. Please setup support
nodes and then restart this script.
""")

    #If this is not the first node then connect them to the network
    if firstNode == 'n':
      print """
As this node is not the first node in the network please enter connection
information for any other node in the network.
"""
      clusterName = getInput("Enter cluster name: ", str, lambda x: True)
      clusterKey  = getInput("Enter cluster key: ", str, lambda x: True)
      mN.clusterName = clusterName
      mN.clusterKey  = clusterKey

      tries = 0
      #Allow the user to try to connect to the network up to 5 times then give up
      while tries < 5:
        def checkIP(ip):
          import re
          if re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', ip):
            return True
          else:
            return False

        ip = getInput("IP addres: ", str, checkIP)
        port = getInput("Port: ", int, lambda x: True)

        print "\nTrying to connect to the managment network...\n"
        try:
          client = mN.connect(ip, port)
          break
        except Exception as e:
          print e

          import traceback
          tb = traceback.format_exc()
          print tb
          print "Connecting to network failed"
          tries += 1

      #Die if we ran out of tries
      if tries == 5:
        sys.exit("Max number of attempts exceeded")

      print """
Connection established waiting for remote node to verify...
"""

      #Busy wait with timeout
      timeout = 0
      while not client.accepted:
        if timeout == 30:
          #Timeout at 30 seconds
          sys.exit("Timeout exceeded")
        time.sleep(1)
        timeout += 1

      print """
Connection accepted. Initializing...
"""

      mN.sendClientMessage(client.id, ManageNode.INITIALIZE_REQUEST, None)
      #Busy wait with timeout
      timeout = 0
      while not mN.initialized:
        if timeout == 30:
          #Timeout at 30 seconds
          sys.exit("Timeout exceeded")
        time.sleep(1)
        timeout += 1

      print """
================================================================================
= SUCCESS: Connected to the management netowork                                =
================================================================================

The node successfully connected to the management network. This node now knows
about all the other nodes and what services they provide. During the rest of
setup this node can use this information to help make setup easier.

"""
    else:
      print """
================================================================================
= Setting up cluster authentication                                            =
================================================================================
"""
      clusterName = getInput("Enter cluster name: ", str, lambda x: True)
      clusterKey  = getInput("Enter cluster key: ", str, lambda x: True)
      mN.clusterName = clusterName
      mN.clusterKey  = clusterKey
      print """
================================================================================
= Succesfully set up cluster authentication                                    =
================================================================================
"""

    #Based on the choice we spawn a different setup routine
    if choice == 0:
      setupSupport.runSetup(mN)
    else:
      setupApplication.runSetup(mN)

    #Once setup is done we can then just wait for the managment node to be
    #finished
    commandLine(mN)
  finally:
    mN.stop()
    mN.join()
