# coding=utf-8

def commandLine(manageNode):
  print """
Starting interactive command line...
  """

  while True:
    cmd = raw_input("> ")
    if cmd.lower() == "stop":
      break
