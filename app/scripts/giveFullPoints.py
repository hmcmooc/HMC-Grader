import sys

from app.scripts.helpers import *
from app.helpers.autograder import *

from app.structures.models.user import *
from app.userViews.student.submitFiles import createSubmission

from datetime import datetime

if __name__ == "__main__":
  semester = "Spring 15" #raw_input("Course Semester: ")
  courseName = "CS 5" #raw_input("Course Name: ")

  course = getCourse(semester, courseName)

  if course == None:
    print "Could not find the course you specified"
    sys.exit(1)

  for i, a in enumerate(course.assignments):
    print "%d) %s" % (i, a.name)

  index = int(raw_input("Pick an assignment: "))

  assignment = course.assignments[index]

  for i, p in enumerate(assignment.problems):
    print "%d) %s" % (i, p.name)

  index = int(raw_input("Pick a problem: "))

  problem = assignment.problems[index]

  comments = "TEST 42"
  section = "Points"
  score = 42

  students = User.objects.filter(courseStudent=course)

  for s in students:
    print "Student: " + student.username
    sub = problem.getLatestSubmission(s)
    if sub == None:
      sub, _ = createSubmission(problem, s)
      sub.isLate = False
      sub.save()
      problem.save()


    #set the grade
    sub.grade.scores[section] = score
    sub.grade.save()
    sub.comments = comments
    sub.status = SUBMISSION_GRADED
    sub.save()
