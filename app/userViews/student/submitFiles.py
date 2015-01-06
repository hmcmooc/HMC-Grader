# coding=utf-8

#import the app
from app import app

#import flask things
from flask import g, request, render_template, redirect, url_for, flash, abort
from flask.ext.login import current_user, login_required

from werkzeug import secure_filename

#import models
from app.structures.models.user import *
from app.structures.models.gradebook import *
from app.structures.models.course import *

#import forms
from app.structures.forms import SubmitAssignmentForm

#import app helpers
from app.helpers.filestorage import *
from app.helpers.autograder import gradeSubmission

#import other libraries
import os, datetime, shutil

@app.route('/assignments/submit/<pid>')
@login_required
def submitAssignment(pid):
  '''
  Function Type: View Function
  Template: student/submit.html
  Purpose: Allow a student to submit files for a homework assignment problem.

  Inputs:
    pid: The object ID for the problem being submitted to

  Template Parameters:
    course: The course which contains the problem
    assignment: The assignment group containing the problem
    problem: The problem object specified by <pid>
    form: A SubmitAssignmentForm which has had the partner field filled with
    the students from course.

  Forms Handled: None
  '''
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.courseStudent):
      abort(403)

    saf = SubmitAssignmentForm()
    saf.partner.choices = [("None", "None")] + [(str(x.id), x.username) for x in User.objects.filter(courseStudent=c) if not x.username == current_user.username]

    return render_template("student/submit.html", \
                            course=c, assignment=a, problem=p,\
                            form=saf)
  except (Problem.DoesNotExist, Course.DoesNotExist, AssignmentGroup.DoesNotExist):
    #If either p can't be found or we can't get its parents then 404
    abort(404)

#Endpoint for uploading files

@app.route('/assignments/submit/<pid>/upload', methods=['POST'])
@login_required
def uploadFiles(pid):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Create a new submission and put the files in the backing filesystem.
  If a partner is specified create the partner's submission as well and link the
  two submissions.

  Inputs:
    pid: The object ID for the problem to be submitted to.

  Forms Handled:
    SubmitAssignmentForm: Contains the files being submitted and the partner
    choice.
  '''
  try:
    p = Problem.objects.get(id=pid)
    c, a = p.getParents()
    user = User.objects.get(id=g.user.id)
    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.courseStudent):
      abort(403)

    if request.method == "POST":
      form = SubmitAssignmentForm(request.form)
      form.partner.choices = [("None", "None")] + [(str(x.id), x.username) for x in User.objects.filter(courseStudent=c) if not x.username == current_user.username]
      if form.validate():
        #Create the submissions
        userSub, userSubPath = createSubmission(p, user)
        userSub.save()
        if form.partner.data != "None":
          partner = User.objects.get(id=form.partner.data)
          partnerSub, partnerSubPath = createSubmission(p, partner)
          partnerSub.save()

          #Link the submissions
          userSub.partner = partner
          userSub.partnerSubmission = partnerSub
          userSub.save()
          partnerSub.partner = user
          partnerSub.partnerSubmission = userSub
          partnerSub.save()

        #Save the files to the folder
        saveFiles(userSubPath, request.files.getlist("files"))

        if form.partner.data != "None":
          shutil.rmtree(partnerSubPath)
          shutil.copytree(userSubPath, partnerSubPath)

        missingFiles = ensureFiles(p, userSubPath)

        if not len(missingFiles) == 0:
          flash("Some required files are missing from your submission. \
                It has been accepted but autogradign will not run.", "warning")
          for m in missingFiles:
            flash("Missing required file: " + m, "warning")

        #Save our submissions to the database
        p.save()
        p.gradeColumn.save()

        gradeSubmission.delay(p.id, user.id, p.getSubmissionNumber(user))
        if form.partner.data != "None":
          gradeSubmission.delay(p.id, partner.id, p.getSubmissionNumber(partner))
      else:
        flash("We could not validate your submission. If this keeps occurring please contact your professor.", "warning")
    return redirect(url_for('studentAssignments', cid=c.id))
  except (Problem.DoesNotExist, Course.DoesNotExist, AssignmentGroup.DoesNotExist):
    #If either p can't be found or we can't get its parents then 404
    abort(404)
  except User.DoesNotExist:
    flash("We couldn't find the partner you specified.", "error")
    abort(500)

#
# Helpers
#

def saveFiles(filePath, files):
  try:
    for f in files:
      filename = secure_filename(f.filename)
      if filename == "":
        continue
      f.save(os.path.join(filePath, filename))
      processZip(filePath, filename)
  except Exception as e:
    shutil.rmtree(filePath)
    flash("One of your files has caused our system to crash."+\
    " This most commonly happens with zip files which contain two copies of files with the same name or a file which has the same name as the zip file itself."+\
    " Please look at the error and try to correct this issue."+\
    " If this is not your issue please report a bug to the system administrator", "warning")
    raise e

def ensureFiles(problem, filePath):
  reqFiles = problem.getRequiredFiles()
  for root, dirs, files in os.walk(filePath):
    for f in files:
      if f in reqFiles:
        reqFiles.remove(f)
  return reqFiles

def processZip(filePath, fileName):
  from zipfile import ZipFile, is_zipfile
  if not is_zipfile(os.path.join(filePath, fileName)):
    return

  z = ZipFile(os.path.join(filePath, fileName))

  extractPath = os.path.join(filePath, '.extracted')
  z.extractall(extractPath)

  if all([os.path.isdir(os.path.join(extractPath, f)) for f in os.listdir(extractPath)]):
    for d in [ f for f in os.listdir(extractPath) if os.path.isdir(os.path.join(extractPath,f)) ]:
      for f in os.listdir(os.path.join(extractPath, d)):
        shutil.move(os.path.join(extractPath, d, f), filePath)
  else:
    for f in os.listdir(extractPath):
      shutil.move(os.path.join(path, f), filePath)

  shutil.rmtree(os.path.join(filePath, '.extracted'))

def createSubmission(problem, user):
  '''
  Function Type: Helper Function
  Purpose: Create a new submission for a user

  Inputs:
    problem: The problem object for this submission
    user: The user object for this submission
  '''
  #Make sure the user has a submisssion list
  if user.username not in problem.studentSubmissions:
    problem.studentSubmissions[user.username] = StudentSubmissionList()
    problem.save()

  #Create a grade entry
  grade = GBGrade()
  grade.save()
  problem.gradeColumn.scores[user.username] = grade
  problem.gradeColumn.save()

  #Get the submission number
  subNum = len(problem.studentSubmissions[user.username].submissions)+1

  c, a = problem.getParents()
  filePath = getSubmissionPath(c, a, problem, user, subNum)
  ensurePathExists(filePath)

  #Create a submission
  sub = Submission()
  sub.submitter = user
  sub.grade = grade
  sub.problem = problem
  sub.submissionTime = datetime.datetime.utcnow()

  if problem.duedate < sub.submissionTime:
    sub.isLate = True

  sub.save()

  #Set the submission reference in the grade
  grade.submission = sub
  grade.save()

  #Add the submission to the submission list
  problem.studentSubmissions[user.username].addSubmission(sub)

  sub.save()

  return sub, filePath
