# coding=utf-8

import socket
import threading
import select
from multiprocessing import Queue
import json

def default_con_recv(node, msg, clientID):
  client = node.getClient(msg)
  client.accepted = True
  client.start()
  client.sendMsg(Node.CON_ACK, node.listeningAddr)

def default_con_lost(node, msg, clientID):
  del node.clients[clientID]

def default_con_ack(node, msg, clientID):
  client = node.getClient(clientID)
  client.accepted = True
  client.listeningAddr = msg
  client.setnMsg(Node.CON_ACK_RESP, node.listeningAddr)

def default_con_ack_resp(node, msg, clientID):
  client = node.getClient(clientID)
  client.accepted = True
  client.listeningAddr = msg

class Node(threading.Thread):
  CON_RECV = 'con_recv'
  CON_LOST = 'con_lost'
  CON_ACK = 'con_ack'
  CON_ACK_RESP = 'con_ack_resp'

  def __init__(self, host, port, stopPoll=0.5):
    #Initialize our threadness
    threading.Thread.__init__(self)
    #Create a queue for incoming messages from our connected nodes
    self.queue = Queue()

    #create the server socket
    self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.server.bind((host, port))
    self.server.listen(5)

    self.running = True
    self.stopPoll = stopPoll

    #stuff for managing clients
    self.clients = {}
    self.clientNumLock = threading.Lock()
    self.clientNum = 0

    if host != '':
        self.listeningAddr = (host, port)
    else:
        self.listeningAddr = (socket.gethostbyname(socket.gethostname()), port)

    #create the message dispatch table
    self.dispatch = {Node.CON_RECV: default_con_recv,
    Node.CON_LOST: default_con_lost,
    Node.CON_ACK: default_con_ack,
    Node.CON_ACK_RESP: default_con_ack_resp}

  def run(self):
    while self.running:
      inputs = [self.server, self.queue._reader]
      iready, oready, eready = select.select(inputs, [], [], self.stopPoll)

      for s in iready:
        if s == self.server:
          #accept a new connection
          newClient = ConnectionClient(self.server.accept(), self.queue, self.getClientNum(), self.stopPoll)
          self.clients[newClient.id] = newClient
          #Send ourselves a connection recieved msg
          #This is where we will start the
          self.queue.put((Node.CON_RECV, newClient.id, -1))
        else:
          msgType, msg, client = self.queue.get()
          if msgType in self.dispatch:
            self.dispatch[msgType](self, msg, client)
          else:
            print >> sys.stderr, "Recieved message that has no associated handler"


    #Kill the server socket when done
    self.server.close()

  def stop(self):
    for c in self.clients:
      self.clients[c].stop()
      if self.clients[c].is_alive():
        self.clients[c].join()
    self.running = False

  #A decorator for adding handlers to the node
  def handle(self, msgType):
    def make_handler(handler):
      self.dispatch[msgType] = handler
      return handler
    return make_handler

  #For sending a message to the ndoe thread not over the network
  def localMessage(self, msgType, msg):
    self.queue.put((msgType, msg, -1))

  def connect(self, host, port):
    addr = (host, port)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(addr)
    newClient = ConnectionClient((s, addr), self.queue, self.getClientNum(), self.stopPoll)
    newClient.start()
    self.clients[newClient.id] = newClient

  def sendClientMessage(self, clientID, msgType, msg):
    client = self.clients[clientID]
    client.sendMsg(msgType, msg)

  def getClientNum(self):
    self.clientNumLock.acquire()
    out = self.clientNum
    self.clientNum += 1
    self.clientNumLock.release()
    return out

  def getClient(self, num):
    if num in self.clients:
      return self.clients[num]
    else:
      return None

class ConnectionClient(threading.Thread):
  def __init__(self, (socket, addr), queue, id, stopPoll=0.5):
    threading.Thread.__init__(self)
    self.client = socket.makefile('r+b', bufsize=1024)
    self.addr = addr
    self.queue = queue
    self.running = True
    self.msgQueue = Queue()
    self.accepted = False
    self.stopPoll = stopPoll
    self.id = id
    self.listeningAddr = None
    pass

  def run(self):
    while self.running:
      inputs = [self.client, self.msgQueue._reader]
      iready, oready, eready = select.select(inputs, [self.client], [], self.stopPoll)

      for s in iready:
        if s == self.client:
          data = self.client.readline().strip()
          if data == '': #We lost the connection so we should terminate
            self.queue.put((Node.CON_LOST, None, self.id))
            self.running = False
            break
          else:
            msgType, msg = json.loads(data)
            self.queue.put((msgType, msg, self.id))
        if s == self.msgQueue._reader and self.client in oready:
          self.client.write(json.dumps(self.msgQueue.get()) + '\n')
          self.client.flush()

    #close socket when done
    self.client.close()

  def stop(self):
    self.running = False

  def sendMsg(self, msgType, msg):
    self.msgQueue.put((msgType, msg))
