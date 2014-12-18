# -*- coding: utf-8 -*-

'''
This module contains the view functions for the grutor module
'''

#import the app and the login manager
from app import app, loginManager

#Standard flask importsi
from flask import g, request, render_template, redirect, url_for, flash, abort
from flask.ext.login import login_user, logout_user, current_user, login_required

#Import models needed for these pages
from app.structures.models.user import *
from app.structures.models.gradebook import *
from app.structures.models.course import *

#Generic python imports
import os, datetime, fcntl, random
from werkzeug import secure_filename

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
      abort(403)

    return render_template("grutor/assignments.html", course=c)
  except Course.DoesNotExist as e:
    abort(404)

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
      abort(403)

    #Get the students for this course
    students = User.objects.filter(courseStudent=c)

    return render_template("grutor/problems.html", \
                            course=c, problem=p, assignment=a, users=students)
  except Course.DoesNotExist as e:
    abort(404)

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
      abort(403)

    #p = Problem.objects.get(id=pid)
    #a = AssignmentGroup.objects.get(id=aid)

    submission = p.getSubmission(user, subnum)

    u = User.objects.get(id=g.user.id)

    #If this is not in progress by anyone try to claim it atomically
    if submission.status < 3:
      subCol = Submission._get_collection()
      res = subCol.find_and_modify(query={'_id':submission.id, 'status_lt': 3}, update={"$set": {"status":3, "gradedBy": u.id}})
      #submission.gradedBy = u
      if res == None:
        flash("It appears another grader has already claimed this assignment are you sure you want to grade it?", "warning")
    elif submission.gradedBy != u:
      flash("It appears another grader has already claimed this assignment are you sure you want to grade it?", "warning")

    submission.status = max(submission.status, 3)

    if submission.partnerInfo != None:
      if submission.partnerInfo.submission.status < 3:
        submission.partnerInfo.submission.gradedBy = u
      submission.partnerInfo.submission.status = max(submission.partnerInfo.submission.status, 3)
      submission.partnerInfo.submission.save()

    submission.save()

    p.save()

    return render_template("grutor/gradesubmission.html", \
                            course=c, problem=p, assignment=a, subnum=subnum,
                            user=user, submission=submission)
  except Course.DoesNotExist as e:
    abort(404)

@app.route('/grutor/gradebook/<cid>')
@login_required
def grutorViewGradebook(cid):
  '''
  Function Type: View Function
  Template: instructor/gradebook.html
  Purpose: Display all of the grades for this course. Allow for creation of
  arbitrary submission entries.

  Inputs:
    cid: The object ID of the course to display

  Template Parameters: TODO

  Forms Handled: TODO
  '''
  try:
    c = Course.objects.get(id=cid)
    if not (g.user.isAdmin or c in current_user.gradingCourses()):
      abort(403)

    #Get the users for this course
    s = User.objects.filter(courseStudent=c)


    s = list(s)
    s.sort(key=lambda x:x.username)
    uids = [str(u.id) for u in s]

    return render_template('grutor/gradebook.html', course=c, uids=uids)
  except Course.DoesNotExist:
    abort(404)

@app.route('/grutor/gradebook/<cid>/<col>')
@login_required
def grutorEditGradebook(cid, col):
  '''
  Function Type: View Function
  Template: grutor/editcolumn.html
  Purpose: Allows the grutor to edit one column of the gradebook manually

  Inputs:
    cid: The object ID of the course to authenticate the grader
    col: The object ID of the column to be edited

  Template Parameters: TODO
  '''

  try:
    course = Course.objects.get(id=cid)
    column = GBColumn.objects.get(id=col)

    if not (course in current_user.gradingCourses() or current_user.isAdmin):
      abort(403)

    users = User.objects.filter(courseStudent=course)

    for u in users:
      if not u.username in column.scores:
        flash("Creating")
        grade = GBGrade()
        grade.scores['score'] = 0
        grade.save()
        column.scores[u.username] = grade

    column.save()

    return render_template("grutor/editcolumn.html", course = course, col=column, users=users)
  except Course.DoesNotExist:
    abort(404)
  except GBColumn.DoesNotExist:
    flash("The gradebook column you requested no longer exists")
    abort(404)
