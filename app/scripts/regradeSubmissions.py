import sys

from app.scripts.helpers import *
from app.helpers.autograder import *

if __name__ == "__main__":
  semester = raw_input("Course Semester: ")
  courseName = raw_input("Course Name: ")

  course = getCourse(semester, courseName)

  if course == None:
    print "Could not find the course you specified"
    sys.exit(1)

  assignments = [x.name for x in course.name]

  for i, a in enumerate(assignments):
    print "%d) %s" % (i, a.name)
