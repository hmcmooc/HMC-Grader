import sys

from app.scripts.helpers import *
from app.helpers.autograder import *

from app.structures.models.user import *
from app.userViews.student.submitFiles import createSubmission

from datetime import datetime

if __name__ == "__main__":
  courseName = raw_input("Course Name: ")
  semester = raw_input("Course Semester: ")

  course = getCourse(semester, courseName)

  if course == None:
    print "Could not find the course you specified"
    sys.exit(1)

  try:
    while True:
      uid = raw_input("ID to identify: ")
      found = False
      for k, v in course.anonIds.iteritems():
        if v == uid:
          u = User.objects.get(username=k)
          print "\nUsername: %s" % (u.username)
          print "First Name: %s" % (u.firstName)
          print "Last Name: %s" % (u.lastName)
          print "Email: %s\n\n" % (str(u.email))
          found = True
          break
      if found:
        continue
      print "User not found in this course"
  except EOFError:
    print "Finished"
