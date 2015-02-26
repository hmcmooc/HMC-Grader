# coding=utf-8

import socket, sys, threading, json, time
from multiprocessing import Queue
from base64 import b64encode, b64decode

#Import gevent stuff
import gevent
from gevent import select, Greenlet

#
# The following functions define the connection establishment protocol
#

#Established node recieves a connection from a new client
def default_con_recv(node, msg, clientID):
  client = node.getClient(clientID)
  client.start()
  client.sendMsg(Node.AUTH_REQ, None)

#Established node recieves a connection from a new client and we are using
#encryption
def encrypt_con_recv(node, msg, clientID):
  client = node.getClient(clientID)
  client.start()
  client.sendMsg(Node.PUB_REQ, None)

#connecting node handles a request for a public key from the
#already established node
def encrypt_pub_req(node, msg, clientID):
  client = node.getClient(clientID)
  from Crypto.PublicKey import RSA
  from Crypto.Cipher import PKCS1_OAEP
  key = RSA.generate(1024)
  #Get the public key to send to the established node
  pub = key.publickey()
  #store the public key
  client.pubKey = key
  #Send the public key
  client.sendMsg(Node.PUB_RESP, pub.exportKey('PEM'))

#Established node recieves a public key from the connecting node
def encrypt_pub_resp(node, msg, clientID):
  client = node.getClient(clientID)
  from Crypto.PublicKey import RSA
  from Crypto.Cipher import PKCS1_OAEP
  from Crypto import Random
  client.key = Random.new().read(32)
  #Make the encoder
  key = RSA.importKey(msg)
  enc = PKCS1_OAEP.new(key)
  #encode the key for transmission with the public key
  encMsg = enc.encrypt(client.key)
  encMsg = b64encode(encMsg)
  client.sendMsg(Node.KEY_SEND, encMsg)


#Connecting client handles getting an encrypted key from the established
#node
def encrypt_key_send(node, msg, clientID):
  client = node.getClient(clientID)
  from Crypto.Cipher import PKCS1_OAEP
  dec = PKCS1_OAEP.new(client.pubKey)
  client.key = dec.decrypt(b64decode(msg))
  #Bypass the queue to prevent encryption deadlock
  client.putMsg((Node.KEY_ACK, None))
  client.encEnabled = True
  pass

#Established node handles and acknowledgement from the connecting node that
#it now has the key
def encrypt_key_ack(node, msg, clientID):
  client = node.getClient(clientID)
  client.encEnabled = True
  client.sendMsg(Node.AUTH_REQ, None)

#Connecting node handles a request for authentication
def default_auth_req(node, msg, clientID):
  client = node.getClient(clientID)
  #Send the response of whatever the authFunc returns
  client.sendMsg(Node.AUTH_RESP, node.authFunc())

#Established node handles an authentication response from the connecting node
def default_auth_resp(node, msg, clientID):
  client = node.getClient(clientID)

  if node.authCheck(msg):
    client.accepted = True
    client.sendMsg(Node.CON_ACK, node.listeningAddr)

#
# If anything is going to be overloaded it should be these ones
# They are really where you can start communicating with user code before
# this point it is easy to mess up the handshake
#

#Connecting node gets an acknoledgement of connection
def default_con_ack(node, msg, clientID):
  client = node.getClient(clientID)
  client.accepted = True
  client.listeningAddr = msg
  client.sendMsg(Node.CON_ACK_RESP, node.listeningAddr)

#Established node gets response ack from connecting node
def default_con_ack_resp(node, msg, clientID):
  client = node.getClient(clientID)
  client.listeningAddr = msg
  client.accepted = True

#A node handles losing a connection to a client
def default_con_lost(node, msg, clientID):
  del node.clients[clientID]

def default_connect(node, msg, clientID):
  addr = msg
  try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(addr)
    newClient = ConnectionClient.spawn((s, addr), node.queue, clientID, node.stopPoll)
    node.clients[newClient.id] = newClient
  except Exception as e:
    node.clients[clientID] = e

class Node(threading.Thread):
  CON_RECV      = 'node_con_recv'
  CON_LOST      = 'node_con_lost'
  PUB_REQ       = 'node_pub_key_req'
  PUB_RESP      = 'node_pub_key_resp'
  KEY_SEND      = 'node_sym_key_send'
  KEY_ACK       = 'node_sym_key_ack'
  AUTH_REQ      = 'node_auth_req'
  AUTH_RESP     = 'node_aut_resp'
  CON_ACK       = 'node_con_ack'
  CON_ACK_RESP  = 'node_con_ack_resp'

  CONNECT       = 'node_connect'

  def __init__(self, host, port, encrypt=False, stopPoll=0.5):
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

    #Are we using encryption
    self.encrypt = encrypt

    if host != '':
      self.listeningAddr = (host, port)
    else:
      self.listeningAddr = (socket.gethostbyname(socket.gethostname()), port)

    #create the message dispatch table
    self.dispatch = {
    Node.CON_RECV: default_con_recv,
    Node.AUTH_REQ: default_auth_req,
    Node.AUTH_RESP: default_auth_resp,
    Node.CON_ACK: default_con_ack,
    Node.CON_ACK_RESP: default_con_ack_resp,
    Node.CON_LOST: default_con_lost,
    Node.CONNECT: default_connect}

    if self.encrypt:
      self.dispatch[Node.CON_RECV]  = encrypt_con_recv
      self.dispatch[Node.PUB_REQ]   = encrypt_pub_req
      self.dispatch[Node.PUB_RESP]  = encrypt_pub_resp
      self.dispatch[Node.KEY_SEND]  = encrypt_key_send
      self.dispatch[Node.KEY_ACK]   = encrypt_key_ack

    self.authFunc = lambda: None
    self.authCheck = lambda x: True

  def run(self):
    while self.running:
      inputs = [self.server, self.queue._reader]
      iready, oready, eready = select.select(inputs, [], [], self.stopPoll)
      for s in iready:
        if s == self.server:
          #accept a new connection
          newClient = ConnectionClient(self.server.accept(), self.queue, \
                              self.getClientNum(), self.encrypt, self.stopPoll)
          self.clients[newClient.id] = newClient
          #Send ourselves a connection recieved msg
          #This is where we will start the
          self.queue.put((Node.CON_RECV, None, newClient.id))
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
    newClientNum = self.getClientNum()
    self.queue.put((Node.CONNECT, (host, port), newClientNum))
    #Wait for the connection
    while not newClientNum in self.clients:
      time.sleep(10.0/1000.0)

    if issubclass(type(self.clients[newClientNum]), Exception):
      #If it was an exception clean them out of the dictionary and raise
      # the exception
      e = self.clients[newClientNum]
      del self.clients[newClientNum]
      raise e

    #Otherwise return the client
    return self.clients[newClientNum]


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

class ConnectionClient(Greenlet):
  def __init__(self, (socket, addr), queue, id, encrypt=False, stopPoll=0.5):
    Greenlet.__init__(self)
    self.client = socket.makefile('r+b', bufsize=1024)
    self.addr = addr
    self.queue = queue
    self.running = True
    self.msgQueue = Queue()
    self.accepted = False
    self.stopPoll = stopPoll
    self.id = id
    self.listeningAddr = None
    self.encrypt = encrypt
    #Encryption stuff
    self.pubKey = None
    self.key = None
    self.encEnabled = False
    pass

  def run(self):
    while self.running:
      inputs = [self.client, self.msgQueue._reader]
      iready, oready, eready = select.select(inputs, [self.client], [self.client], self.stopPoll)

      def postFailure():
        self.queue.put((Node.CON_LOST, None, self.id))
        self.running = False

      if len(eready) > 0:
        postFailure()
        break

      for s in iready:
        if s == self.client:
          data = self.client.readline().strip()
          if data == '': #We lost the connection so we should terminate
            postFailure()
            break
          else:
            self.getMsg(data)
        if s == self.msgQueue._reader and self.client in oready:
          self.putMsg(self.msgQueue.get())

    #close socket when done
    self.client.close()

  def putMsg(self, msg):
    msgText = json.dumps(msg)
    if self.encEnabled:
      from Crypto.Cipher import AES
      from Crypto import Random
      iv = Random.new().read(AES.block_size)
      cipher = AES.new(self.key, AES.MODE_CFB, iv)
      msgText = iv + cipher.encrypt(msgText)
      msgText = b64encode(msgText)

    self.client.write(msgText + '\n')
    self.client.flush()

  def getMsg(self, data):
    if self.encEnabled:
      from Crypto.Cipher import AES
      data = b64decode(data)
      iv = data[:AES.block_size]
      data = data[AES.block_size:]
      cipher = AES.new(self.key, AES.MODE_CFB, iv)
      data = cipher.decrypt(data)

    msgType, msg = json.loads(data)
    self.queue.put((msgType, msg, self.id))

  def stop(self):
    self.running = False

  def sendMsg(self, msgType, msg):
    self.msgQueue.put((msgType, msg))
