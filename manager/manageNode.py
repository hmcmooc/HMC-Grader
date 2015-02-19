# coding=utf-8

from node import *


#Overloading the typical RECIVE, LOST, and ACK to add some features for this
#system

def handle_con_recv(node, msg, clientID):
  client = node.getClient(msg)
  client.accepted = True
  client.start()
  out = {}
  out['listeningAddr'] = node.listeninAddr
  #Notify the new node if you provide any services
  out['providesDB'] = node.providesDB == -1
  out['providesFS'] = node.providesFS == -1
  out['providesQ']  = node.providesQ  == -1
  client.sendMsg(Node.CON_ACK, out)

#TODO: Change this to handle losing key components
def handle_con_lost(node, msg, clientID):
  del node.clients[clientID]


def handle_con_ack(node, msg, clientID):
  client = node.getClient(clientID)
  client.accepted = True
  client.listeningAdder = msg['listeningAddr']
  #Fill out our table of who provides what
  if msg['providesDB']:
    node.providesDB = clientID

  if msg['providesFS']:
    node.providesFS = clientID

  if msg['providesQ']:
    node.providesQ = clientID


#For handling: initialize_request
def handle_initialize_request(node, msg, clientID):
    client = node.getClient(clientID)

    #If this client is gone we simply ignore the request
    if client == None:
        return

    clients = [lambda x: x.listeningAddr for x in node.clients.items() if not x == client]

    client.sendMsg(INITIALIZE_RESPONSE, clients)

def handle_initialize_response(node, msg, clientID):
    #If we are initialized already just ignore extra messages s
    if node.initialized:
        return

    node.initialized = True

    #We should be given a list of all of the nodes in the network
    #We then connect to all of these nodes
    for client in msg:
      node.connect(client[0], client[1])


class ManageNode(Node):
  INITIALIZE_REQUEST = "init_req"
  INITIALIZE_RESPONSE = "init_resp"

  def __init__(self, host, port):
      Node.__init__(self, host, port)

      #Has this node recieved an initialization response
      self.initialized = False

      #ID's of clients who provide these services
      #If this node provides that service the value is -1
      #If no node provides the service the value is None
      self.providesDB = None
      self.providesFS = None
      self.providesQ  = None

      #Set up the dispatch table
      self.dispatch[Node.CON_RECV] = handle_con_recv
      self.dispatch[Node.CON_LOST] = handle_con_lost
      self.dispatch[Node.CON_ACK]  = handle_con_ack
      self.dispatch[ManageNode.INITIALIZE_REQUEST] = handle_initialize_request
      self.dispatch[ManageNode.INITIALIZE_RESPONSE] = handle_initialize_response
