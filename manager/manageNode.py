# coding=utf-8

from node import *

#Overloading the typical LOST, AUTH, and ACK to add some features for this
#system

def handle_con_lost(node, msg, clientID):
  client = node.getClient(clientID)

  if clientID == node.providesDB:
    node.providesDB = None
    node.dbInfo = None

  if clientID == node.providesFS:
    node.providesFS = None
    node.fsInfo = None

  if clientID == node.providesQ:
    node.providesQ = None
    node.qInfo = None

  del node.clients[clientID]

  checkUnready(node)

#Established node recieves auth response from connecting node
def handle_auth_response(node, msg, clientID):
  client = node.getClient(clientID)
  if node.authCheck(msg):
    client.accepted = True
    out = {}
    out['listeningAddr'] = node.listeningAddr
    #Notify the new node if you provide any services
    out['providesDB'] = node.providesDB == -1
    out['providesFS'] = node.providesFS == -1
    out['providesQ']  = node.providesQ  == -1
    client.sendMsg(Node.CON_ACK, out)

#If someone we connected to provides something register that and check if we
#are ready
def handle_con_ack(node, msg, clientID):
  client = node.getClient(clientID)
  client.accepted = True
  client.listeningAddr = msg['listeningAddr']
  #Fill out our table of who provides what
  if msg['providesDB']:
    node.providesDB = clientID

  if msg['providesFS']:
    node.providesFS = clientID

  if msg['providesQ']:
    node.providesQ = clientID

  client.sendMsg(Node.CON_ACK_RESP, node.listeningAddr)
  checkReady(node)


#For handling: initialize_request
def handle_initialize_request(node, msg, clientID):
  client = node.getClient(clientID)
  #For "Security"
  if not client.accepted:
    return

  #If this client is gone we simply ignore the request
  if client == None:
      return

  clients = [x.listeningAddr for x in node.clients.values() if not x == client]

  client.sendMsg(ManageNode.INITIALIZE_RESPONSE, clients)

def handle_initialize_response(node, msg, clientID):
  #If we are initialized already just ignore extra messages s
  if node.initialized:
      return

  node.initialized = True

  #We should be given a list of all of the nodes in the network
  #We then connect to all of these nodes
  for client in msg:
    node.connect(client[0], client[1])

#PROVIDES_MSG: If we get a provides message add that provider and
#check if we are ready
def handle_provides_msg(node, msg, clientID):
  client = node.getClient(clientID)

  if msg == "DB":
    node.providesDB = clientID
  elif msg == "FS":
    node.providesFS = clientID
  elif msg == "Q":
    node.providesQ = clientID

  checkReady(node)


#INFO_REQ
def handle_info_request(node, msg, clientID):
  client = node.getClient(clientID)

  #For security only let accepted clients connect
  if not client.accepted:
    return

  #Handle the message request but only if we are the provider of that service
  if msg['req'] == "DB" and node.providesDB == -1:
    client.sendMsg(ManageNode.INFO_RESPONSE, ["DB", node.dbInfo])
  elif msg['req'] == "FS" and node.providesFS == -1:
    from os.path import join
    #Add their key to the authorized_keys file
    with open(join('/home', node.fsInfo['user'], '.ssh/authorized_keys'), 'a') as f:
      f.write(msg['key'] + '\n')

    #Send them the connection information
    client.sendMsg(ManageNode.INFO_RESPONSE, ["FS", node.fsInfo])
  elif msg['req'] == "Q" and node.providesW == -1:
    client.sendMsg(ManageNode.INFO_RESPONSE, ["Q", node.qInfo])


def handle_info_response(node, msg, clientID):
  client = node.getClient(clientID)

  #For security only let accepted clients connect
  if not client.accepted:
    return

  if msg[0] == "DB":
    self.dbInfo = msg[1]
  elif msg[0] == "FS":
    self.fsInfo = msg[1]
  elif msg[0] == "Q":
    self.qInfo = msg[1]

  checkReady(node)

#Check if we are ready
#REady means that we have all provides and
def checkReady(node):
  #If we are missing a provide then don't do anything
  if node.providesDB == None or \
     node.providesFS == None or \
     node.providesQ  == None:
    return

  if node.dbInfo == None:
    node.sendClientMessage(node.providesDB, MessageNode.INFO_REQUEST, {'req': "DB"})
    return

  if node.fsInfo == None:
    node.sendClientMessage(node.providesFS, MessageNode.INFO_REQUEST, {'req': "FS", "key":""})
    return

  if node.qInfo == None:
    node.sendClientMessage(node.providesQ, MessageNode.INFO_REQUEST, {'req': "Q"})
  pass

def checkUnready(node):
  pass

class ManageNode(Node):
  INITIALIZE_REQUEST      = "init_req"
  INITIALIZE_RESPONSE     = "init_resp"
  PROVIDES_MSG            = "provides"
  INFO_REQUEST            = "info_req"
  INFO_RESPONSE           = "info_resp"

  def __init__(self, host, port):
      Node.__init__(self, host, port, True)

      #Authentication information
      self.clusterName = None
      self.clusterKey = None
      self.authFunc = lambda: [self.clusterName, self.clusterKey]
      self.authCheck = lambda x: x == self.authFunc()

      #Has this node recieved an initialization response
      self.initialized = False

      #ID's of clients who provide these services
      #If this node provides that service the value is -1
      #If no node provides the service the value is None
      self.providesDB = None
      self.providesFS = None
      self.providesQ  = None

      #Info dictionaries for storing useful data
      self.dbInfo = None
      self.fsInfo = None
      self.qInfo  = None


      #Client side information
      self.publicKey = None

      #Set up the dispatch table
      self.dispatch[Node.CON_LOST] = handle_con_lost
      self.dispatch[Node.AUTH_RESP] = handle_auth_response
      self.dispatch[Node.CON_ACK]  = handle_con_ack
      self.dispatch[ManageNode.INITIALIZE_REQUEST] = handle_initialize_request
      self.dispatch[ManageNode.INITIALIZE_RESPONSE] = handle_initialize_response
