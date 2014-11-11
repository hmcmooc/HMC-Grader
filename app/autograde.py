# coding=utf-8

from app import app, celery, db
from models.user import User
from models.course import Problem , Course, AssignmentGroup
from models.gradebook import GBGrade

import os,shutil, json
from decimal import *
from subprocess import Popen, PIPE
from datetime import datetime

from app.autograder import getTestResultParsers

from app.filestorage import *

@celery.task()
def gradeSubmission(pid, uid, subnum):
  try:
    user = User.objects.get(id=uid)
    problem = Problem.objects.get(id=pid)
    course, assignment = problem.getParents()

    #First check if tests have even been assigned
    if len(problem.testfiles) == 0:
      #If there are none we are done
      sub = problem.getSubmission(user, subnum)
      #Set the status as awaiting grader unless it is already at a higher point
      #than that
      sub.status = max(sub.status, 2)
      sub.save()
      return

    #Create the directory name for the testing files
    #In the form COURSE_ASSIGNMENT_PROBLEM_USER_SUBNUM to prevent conflicts with
    #rapid submissions
    testDirName = "_".join([course.name, assignment.name, problem.name, user.username, str(subnum)])
    #Remove spaces from the name
    testDirName = "-".join(testDirName.split())
    #Make the path for the test dir
    testDirPath = os.path.join("/tmp", testDirName)

    #Make the testing directory and move to it
    os.mkdir(testDirPath)
    os.chdir(testDirPath)

    #Get all submitted files and put them in the temp directory
    submissionDir = getSubmissionPath(course, assignment, problem, user, subnum)
    testsDir = getTestPath(course, assignment, problem)
    submittedFiles = [f for f in os.listdir(submissionDir) if os.path.isfile(os.path.join(submissionDir, f))]

    #Move the files
    for f in submittedFiles:
      shutil.copy(os.path.join(submissionDir, f), testDirPath)

    #Move the test files
    #NOTE: We move these files second so that if a student submits a file that
    #has the same name as one of the test files it will get overwritten. This
    #is to try to prevent test spoofing where a student could submit a test file
    #in which all tests trvially pass. (Not that that should happen with Mudders
    #but we want to be secure none the less)
    for f in problem.testfiles:
      shutil.copy(os.path.join(testsDir,f), testDirPath)
      shutil.copy(os.path.join(testsDir,f)+".json", testDirPath)

    #Get the submission so we can print results
    sub = problem.getSubmission(user, subnum)

    sub.comments = \
"""
# Grader #
* * *
# Autograder #

"""

    #Run each test function and parse the results
    for f in problem.testfiles:
      print f
      #TODO: change user to prevent bad things
      with open(f+".json") as spec:
        gradeSpec = json.load(spec)

      #Start a section for this file
      sub.comments += "### " + f + " ###\n"

      try:
        startTime = datetime.now()
        testProc = Popen(['python', f], stdout=PIPE, stderr=PIPE, env=os.environ)

        timeoutReached = False
        while testProc.poll() is None:
          currentTime = datetime.now()
          delta = currentTime - startTime
          if delta.total_seconds() > 30: #TODO: Fix arbitrary timeout limit
            testProc.kill()
            timoutReached = True
            break

        if timeoutReached:
          sub.comments += '<font color="Red">Timeout Occurred</font>\n\n'
          continue #we are done so just do the next file

        testOutput, testError = testProc.communicate()
        summary, failedTests = pythonResultParser(testOutput, testError)

        #Go through the sections and find assign points
        for section in gradeSpec['sections']:
          sub.comments += "#### **Test Section**: " + section['name'] + " ####\n"
          failed = 0
          for test in section['tests']:
            if test in failedTests:
              failed += 1
              sub.comments += '##### <font color="Red">Failed</font>:' + test +" #####\n"
              sub.comments += '<pre>' + failedTests[test]['hint'] + '</pre>\n'
            else:
              sub.comments += '##### <font color="Green">Passed</font>:' + test +" #####\n"

          #Assign the score
          assignedPoints = Decimal(section['points']) * (Decimal(1)-(Decimal(failed)/Decimal(len(section['tests']))))
          print len(section['tests'])
          if section['section'] in sub.grade.scores:
            sub.grade.scores[section['section']] += assignedPoints
          else:
            sub.grade.scores[section['section']] = assignedPoints
      except Exception as e:
        sub.comments += "Error running tests: \n<pre>" + str(e) + "</pre>\n\n"

    #Remove the testing directory and all of the files
    shutil.rmtree(testDirPath)

    print "Saving submission changes"
    #TODO: Actually finish the work now we are just testing filemoving
    sub = problem.getSubmission(user, subnum)
    sub.status = max(sub.status, 2)
    sub.save()

  except (User.DoesNotExist, Problem.DoesNotExist, Course.DoesNotExist, AssignmentGroup.DoesNotExist):
    pass
