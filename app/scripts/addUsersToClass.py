from helpers import addUser, getClass
from app.models import *
import sys

usage = """
Usage:
python addUsersToClass <class name> <user csv file>
"""

if __name__ == '__main__':
  if len(sys.argv) != 3:
    print usage
    sys.exit(0)
  courseName = sys.argv[1]
  studentFile = sys.argv[2]

  course = getClass(courseName)
  #If we didn't find the course just quit
  if course == None:
    sys.exit(0)

  with open(studentFile, 'r') as f:
    for line in f:
      columns = line.split(',')
      u = addUser(email=columns[0], firstName=columns[1], lastName=columns[2],\
                  password=columns[3], username=columns[4])
      u.courseStudent.append(course)
      u.save()
  print "Added all students to the course"
