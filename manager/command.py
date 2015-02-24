# coding=utf-8

from utilities import makeStatusMsg

def commandLine(manageNode):
  print """
Starting interactive command line...
  """

  while True:
    cmd = raw_input("> ")
    if cmd.lower() == "stop":
      break
    elif cmd.lower() == "status":
      print """
================================================================================
= Backing system status                                                        =
================================================================================

Database Status:     %s
File System Status:  %s
Work Queue Status:   %s
""" % (
  makeStatusMsg(manageNode, manageNode.providesDB),
  makeStatusMsg(manageNode, manageNode.providesFS),
  makeStatusMsg(manageNode, manageNode.providesQ)
  )
