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
DB Info: %s
File System Status:  %s
FS Info: %s
Work Queue Status:   %s
Q Info: %s
""" % (
  makeStatusMsg(manageNode, manageNode.providesDB), str(manageNode.dbInfo),
  makeStatusMsg(manageNode, manageNode.providesFS), str(manageNode.fsInfo),
  makeStatusMsg(manageNode, manageNode.providesQ), str(manageNode.qInfo),
  )
