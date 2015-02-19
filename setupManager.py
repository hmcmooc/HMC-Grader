#!/usr/bin/python
# coding=utf-8

"""
This script helps setup and manage a node in the CS> system.

This file is pretty large and has a lot of weird formatting for output purposes
but if you read it it should be pretty self explanatory.
"""

import os, sys, time

from manager import setupSupport, setupApplication
from manager.manageNode import ManageNode

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
    except:
      print "Data couldn't be converted to correct type. Please try again\n"
      tries += 1
      continue

  sys.exit("Maximum number of tries exceeded exiting program")



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

  port = getInput("Enter port number (Default 9050): ", str, checkPort)

  #If the port is empty set it to the default otherwise use the port
  if port == '':
    port = 9050
  else:
    port = int(port)

  #Spawn the node object
  mN = ManageNode('', port)
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
      tries = 0
      #Allow the user to try to connect to the network up to 5 times then give up
      while tries < 5:
        def checkIP(ip):
          import re
          if re.match(r'\d{3}\.\d{3}\.\d{3}\.\d{3}'):
            return True
          else:
            return False

        ip = getInput("IP addres: ", str, checkIP)
        port = getInput("Port: ", int, lambda x: True)

        print "\nTrying to connect to the managment network...\n"
        try:
          mN.connect(ip, port)
          break
        except:
          print "Connecting to network failed"
          tries += 1
          continue

      #Die if we ran out of tries
      if tries == 5:
        sys.exit("Max number of attempts exceeded")

      print """
Connection established waiting for remote node to verify...
"""

      #Busy wait with timeout
      timeout = 0
      while not mN.clients[0].accepted:
        if timeout == 30:
          #Timeout at 30 seconds
          sys.exit("Timeout exceeded")
        time.sleep(1)
        timeout += 1

      print """
Connection accepted. Initializing...
"""

      #TODO: Initialize here

    #Based on the choice we spawn a different setup routine
    if choice == 0:
      setupSupport.runSetup(mN)
    else:
      setupApplicatoin.runSetup(mN)

    #Once the setup functions are done we should be ready to attach ourselves to
    #the rest of the nodes
  finally:
    mN.stop()
    mN.join()
