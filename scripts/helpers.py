from app.models import *

def createUsername(firstName, lastName):
  return firstName[0]+lastName

def addUser(username=None, firstName="", lastName="",
            email="", password="asdf"):
  '''This function attempts to create a new user. If a user with that name
  already exists it will provide an interactive prompt requesting a different
  username'''
  #Create the username if it isn't providied
  if username == None:
    #Make sure a name was provided or else error out
    if len(firstName) == 0 or len(lastName) == 0:
      print "No username or first/last name provided skipping user"
      return None
    #Otherwise we create a username dynamically
    username = createUsername(firstName, lastName)

  #Check if the user exists
  try:
    #Leverage the exception to break us out of the loop when we get a good
    #username
    while True:
      User.objects.get(username=username)
      print "User with username: %s already exists" % (username)
      username = raw_input("Please provide a new username: ")
  except:
    #nothing to do this is good
    pass

  #create the user
  u = User()
  u.username = username
  u.firstName = firstName
  u.lastName = lastName
  u.email = email
  u.setPassword(password)
  u.save()
  #return the user when we are done
  print "Added user: %s" % (username)
  return u

def getClass(classname):
  try:
    return Course.objects.get(name=classname)
  except:
    print "Course not found"
    return None
