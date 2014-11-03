# -*- coding: utf-8 -*-
'''
This module contains all the callback functions for the grutor pages
'''

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for, flash, send_file, jsonify
from flask.ext.login import login_user, logout_user, current_user, login_required

from flask.ext.mongoengine import DoesNotExist

from werkzeug import secure_filename

from app.models import *
from app.forms import SubmitAssignmentForm

import os, datetime, fcntl, random
import markdown

from app.filestorage import *

@app.route('/grutor/grade/<pid>/random')
@login_required
def grutorGradeRandom(pid):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Select an ungraded student submission and claim it for the current
  grader. If it selects a student without a submission one is created.

  Inputs:
    pid: The object ID of the problem that is being graded

  Forms Handled: None
  '''
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security we redirect anyone who shouldn't be here to the index
    if not (c in current_user.gradingCourses()):
      return redirect(url_for('index'))

    #create a path to the lockfile
    filepath = getProblemPath(c, a, p)
    if not os.path.isdir(filepath):
      os.makedirs(filepath)
    filepath = os.path.join(filepath, '.lock')
    students = User.objects.filter(courseStudent=c)
    #Open the file and get a writelock to serialize
    with open(filepath, 'w+') as f:
      fcntl.flock(f, fcntl.LOCK_EX)

      def getSubmission(name):
        if name in p.studentSubmissions:
          return (name, p.studentSubmissions[name].submissions[-1], len(p.studentSubmissions[name].submissions))
        else:
          return (name, None, 1)

      #Find an ungraded assignment
      submissions = map(lambda x: getSubmission(x.username), students)
      #Get only submissions that can be graded
      #Define a small predicate to use in the filter
      def isGradeable(submission):
        #get the submission from the tuple
        sub = submission[1]
        #Handle submissions with nothing attached
        if sub == None:
          return True
        if sub.status == 2:
          return True
        else:
          return False

      submissions = filter(isGradeable, submissions)
      if len(submissions) == 0:
        #If there are none to pick redirect and notify
        flash("All submissions have been claimed")
        fcntl.flock(f, fcntl.LOCK_UN)
        return redirect(url_for('grutorGradelistProblem', pid=pid))

      #To prevent race conditions we claim these before the lock is released
      #even though this also happens when we redirect
      subTuple = random.choice(submissions)
      sub = subTuple[1]
      #Handle a non submission
      if sub == None:
        flash("This student submitted nothing. A blank submission has been created")
        #Leverage this function to create stuff for us
        grutorMakeBlank(pid, User.objects.get(username=subTuple[0]).id)
      else:
        sub.status = 3
        sub.save()
        if sub.partnerInfo != None:
          sub.partnerInfo.submission.status = 3
          sub.partnerInfo.submission.save()
      #release the lock
      fcntl.flock(f, fcntl.LOCK_UN)
      #redirect to grading
      #We get the user after releasing the lock to prevent deadlock if this fails
      #for some reason
      user = User.objects.get(username=subTuple[0])
      return redirect(url_for("grutorGradeSubmission", pid=pid, uid=user.id, subnum=subTuple[2]))
  except Exception as e:
    raise e


@app.route('/grutor/finish/<pid>/<uid>/<subnum>')
@login_required
def grutorFinishSubmission(pid, uid, subnum):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Save all the changes to a given submission and return to the
  list of problems.

  Inputs:
    pid: The object ID of the problem this submission belongs to
    uid: The object ID of the user this submission belongs to
    subnum: The submission number for this submission

  Forms Handled: None
  '''
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    user = User.objects.get(id=uid)

    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.gradingCourses()):
      return redirect(url_for('index'))

    #Define a function for performing closing operations
    def finish(sub):
      sub.status = max(sub.status, 4)
      sub.save()
    #End definition

    submission = p.getSubmission(user, subnum)
    finish(submission)

    #Handle the partners submission as well
    #TODO: Make this a function for cleaner code
    if submission.partnerInfo != None:
      finish(submission.partnerInfo.submission)

    p.save()

    return redirect(url_for('grutorGradelistProblem', pid=pid))
  except Exception as e:
    raise e

@app.route('/grutor/release/<pid>/<uid>/<subnum>')
@login_required
def grutorReleaseSubmission(pid, uid, subnum):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Put the submission back so that it may be chosen by another
  grader.

  Inputs:
    pid: The object ID of the problem this submission belongs to
    uid: The object ID of the user this submission belongs to
    subnum: The submission number for this submission

  Forms Handled: None
  '''
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    user = User.objects.get(id=uid)

    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.gradingCourses()):
      return redirect(url_for('index'))

    #Define function for releasing submissions
    def release(sub):
      sub.status = min(submission.status, 2)
      sub.grade.save()
      sub.save()
    #End definition

    submission = p.getSubmission(user, subnum)
    #if not submission.status == 4:
    release(submission)

    if submission.partnerInfo != None:
      release(submission.partnerInfo.submission)

    p.save()

    return redirect(url_for('grutorGradelistProblem', pid=pid))
  except Exception as e:
    raise e

@app.route('/grutor/create/<pid>/<uid>')
@login_required
def grutorMakeBlank(pid, uid):
  '''
  Function Type: Callback-Redirect Function
  Purpose: When a student does not have a submission for a given assignment this
  function is called. It creates a blank submission with no files and then
  redirects the grader to the grade submission page.

  Inputs:
    pid: The object ID for the problem that is being graded.
    uid: The object ID of the user who is being graded.

  Forms Handled: None
  '''
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    user = User.objects.get(id=uid)

    #For security purposes we send anyone who isnt in this class to the index
    if not (c in current_user.gradingCourses()):
      return redirect(url_for('index'))

    #Check that the user we are trying to create a submission for is in the class
    if not (c in user.courseStudent):
      return redirect(url_for('index'))

    #Create a blank submission
    #Create the grade
    grade = GBGrade()
    grade.save()
    p.gradeColumn.scores[user.username] = grade


    p.studentSubmissions[user.username] = StudentSubmissionList()

    #create a filepath
    filepath = getSubmissionPath(c, a, p, user, len(p.studentSubmissions[g.user.username].submissions)+1)

    sub = Submission()
    #Initial fields for submission
    sub.filePath = filepath
    sub.grade = p.gradeColumn.scores[user.username]
    sub.submissionTime = datetime.datetime.utcnow()

    sub.save()
    p.studentSubmissions[user.username].submissions.append(sub)

    #The grader is making this so it isn't late
    sub.isLate = False

    #Create the needed folders
    os.makedirs(filepath)

    p.save(cascade=True)
    return redirect(url_for('grutorGradeSubmission', uid=uid, pid=pid, subnum=1))
  except Course.DoesNotExist as e:
    raise e
