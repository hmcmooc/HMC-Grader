# -*- coding: utf-8 -*-

'''
This module contains the view functions for the grutor module
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

@app.route('/grutor/assignments/<cid>')
@login_required
def grutorAssignments(cid):
  '''
  Function Type: View Function
  Template: grutor/assignments.html
  Purpose: Display all of the assignment groups and problems in those groups
  for the course specified by <cid>.

  Inputs:
    cid: A course object ID

  Template Parameters:
    course: The course object specified by <cid>

  Forms Handled: None
  '''
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt grading this class to the index
    if not ( c in current_user.gradingCourses()):
      return redirect(url_for('index'))

    return render_template("grutor/assignments.html", course=c)
  except Exception as e:
    raise e

@app.route('/grutor/gradelist/problem/<pid>')
@login_required
def grutorGradelistProblem(pid):
  '''
  Function Type: View Function
  Template: grutor/problems.html
  Purpose: Display all of the student submissions for the problem specified by
  <pid>.

  Inputs:
    pid: A problem object ID

  Template Parameters:
    course: The course which contains the problem specified by <pid>
    assignment: The assignment group containing the problem specified by <pid>
    problem: The problem specified by <pid>
    users: A list of the students who are enrolled in <course>

  Forms handled: None
  '''
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.gradingCourses()):
      return redirect(url_for('index'))

    #Get the students for this course
    students = User.objects.filter(courseStudent=c)

    return render_template("grutor/problems.html", \
                            course=c, problem=p, assignment=a, users=students)
  except Exception as e:
    raise e

@app.route('/grutor/grade/<pid>/<uid>/<subnum>')
@login_required
def grutorGradeSubmission(pid, uid, subnum):
  '''
  Function Type: View Function
  Template: grutor/gradesubmission.html
  Purpose: Display to the grader forms that will allow the grader to assign
  grades and give comments on a submission. Additionally allows the grader to
  download the files for the submission.

  Inputs:
    pid: The object ID of the problem being graded
    uid: The object ID of the user whose submission is being graded
    subnum: Which submission of the user is being graded

  Template Parameters:
    course: The course this problem is contained in
    assignment: The assignment group this problem is contained in
    problem: The problem with ID <pid>
    subnum: The submission number that is being graded
    user: The user object specified by <uid>
    submission: The submission object specified by the user, problem, and
    subnum

  Forms Handled: None
  '''
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    user = User.objects.get(id=uid)

    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.gradingCourses()):
      return redirect(url_for('index'))

    #p = Problem.objects.get(id=pid)
    #a = AssignmentGroup.objects.get(id=aid)

    submission = p.getSubmission(user, subnum)
    submission.status = max(submission.status, 3)

    if submission.partnerInfo != None:
      submission.partnerInfo.submission.status = max(submission.partnerInfo.submission.status, 3)
      submission.partnerInfo.submission.save()

    submission.save()

    p.save()

    return render_template("grutor/gradesubmission.html", \
                            course=c, problem=p, assignment=a, subnum=subnum,
                            user=user, submission=submission)
  except Exception as e:
    raise e