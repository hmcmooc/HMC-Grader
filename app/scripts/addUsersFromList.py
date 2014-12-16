import csv, sys, os
from itertools import izip

print os.path.dirname(os.path.realpath(__file__))

from app.scripts.helpers import *

def pairwise(iterable):
    a = iter(iterable)
    return izip(a, a)

if __name__ == "__main__":
  semester = raw_input("Course Semester: ")
  courseName = raw_input("Course Name: ")

  course = getCourse(semester, courseName)

  if course == None:
    print "Could not find the course you specified"
    sys.exit(1)

  userType = raw_input('''
Users should be added as:
0) Students
1) Graders

>>> ''')

  userType = int(userType)

  if userType < 0 and userType > 1:
    print "Not a valid user type"
    sys.exit(1)

  #Actually read the file to get the users info
  with open(sys.argv[1], 'r') as csvFile:
    studentReader = csv.reader(csvFile, delimiter=',', quotechar='"')
    #clear the first 2 rows
    studentReader.next()
    studentReader.next()
    #Get pairs of rows
    for info, name in pairwise(studentReader):
      email = info[4]
      name = name[2]
      #Extract the name parts
      lastName, firstMid = name.split(",")
      firstName = firstMid.strip().split(" ")[0]

      u = addOrGetUser(firstName, lastName, email)
      if userType == 0:
        u.courseStudent.append(course)
      elif userType == 1:
        u.courseGrutor.append(course)
      u.save()
