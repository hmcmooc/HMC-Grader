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


  #Actually read the file to get the users info
  with open(sys.argv[1], 'r') as csvFile:
    studentReader = csv.reader(csvFile, delimiter=',', quotechar='"')

    #Get pairs of rows
    for info in studentReader:
      email = info[5]
      #Extract the name parts
      firstName = info[1]
      lastName = info[0]

      print "%s, %s, %s" %(firstName, lastName, email)

      u = addOrGetUser(firstName, lastName, email)

      u.courseGrutor.append(course)
      u.save()
