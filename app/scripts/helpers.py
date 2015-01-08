from app.structures.models.user import *
from app.structures.models.course import *

def createUsername(firstName, lastName):
  firstName = firstName.lower()
  lastName = lastName.lower()
  #Try increasing the length of the first name to remove conflicts
  for i in range(1,len(firstName)+1):
    try:
      tryName = firstName[:i]+lastName
      u = User.objects.get(username=tryName)
    except User.DoesNotExist:
      return firstName[:i]+lastName

  #If we didn't get a successful name here append numbers
  conflictNumber = 1
  while True:
    try:
      tryName = firstName+lastName+str(conflictNumber)
      u = User.objects.get(username=tryName)
      conflictNumber += 1
    except:
      return firstName+lastName+str(conflictNumber)

def addUser(firstName, lastName, email=None, password="asdf"):
  '''Creates a user with a distinct username'''
  #create the user
  u = User()
  u.username = createUsername(firstName, lastName)
  u.firstName = firstName
  u.lastName = lastName
  u.email = email
  u.setPassword(password)
  u.save()
  #return the user when we are done
  return u

def addOrGetUser(firstName, lastName, email=None, password="asdf"):
  '''If we are given an email try to get an existing user otherwise create
  a new user'''
  if email != None:
    try:
      u = User.objects.get(firstName=firstName, lastName=lastName, email=email)
      return u
    except User.DoesNotExist:
      pass

  return addUser(firstName, lastName, email, password)

def getCourse(semester, name):
  try:
    c = Course.objects.get(semester=semester, name=name)
    return c
  except Course.DoesNotExist:
    return None
