# -*- coding: utf-8 -*-

'''
This module supports operations for instructors to manage courses and assignments
'''

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for, flash, jsonify
from flask.ext.login import login_user, logout_user, current_user, login_required

from flask.ext.mongoengine import DoesNotExist

from app.models import *
from app.forms import CreateAssignmentForm, AddUserCourseForm, ProblemOptionsForm, CourseSettingsForm
from app.filestorage import ensurePathExists, getAssignmentPath, removePath, getProblemPath, getTestPath

import traceback, StringIO, sys
import dateutil.parser

@app.route('/assignment/<cid>/create', methods=['POST', 'GET'])
@login_required
def createAssignment(cid):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Creates a new assignment group with information specified in
  the CreateAssignmentForm.

  Inputs:
    cid: The object ID of the course to add the assignment group to

  Forms Handled:
    CreateAssignmentForm: Verify that an assignment of the same name doesn't
    already exists and then create a new assignment in the course specified by
    <cid>.
  '''
  if request.method == "POST":
    form = CreateAssignmentForm(request.form)
    if form.validate():
      try:
          c = Course.objects.get(id=cid)
          #For security purposes we send anyone who isnt an instructor or
          #admin away
          if not (g.user.isAdmin or c in current_user.courseInstructor):
            return redirect(url_for('index'))

          #If this assignment already exists we want to return now
          if form.name.data in c.assignments:
            flash("Assignment Group already exists")
            return redirect(url_for('administerCourse', id=cid))


          #Create the assignment and problem
          a = AssignmentGroup(form.name.data)
          a.save()
          c.assignments.append(a)

          #Create a GBEntry and GBColumn
          e = GBGroup(form.name.data)
          e.save()
          c.gradeBook.assignmentGrades.append(e)
          #Give the assignment its entry
          a.gradeEntry = e

          #Make sure there is a location on the drive to store this
          ensurePathExists(getAssignmentPath(c,a))

          #Save the documents
          a.save()
          c.save()
          flash("Added Assignment Group")
          return redirect(url_for('administerCourse', cid=cid))
      except Course.DoesNotExist as e:
        raise e
  return redirect(url_for('administerCourse', cid=cid))



@app.route('/assignment/<cid>/<aid>/del')
@login_required
def delAssignment(cid, aid):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Delete an assignment and all problems in that assignment.

  Inputs:
    cid: The object ID of the course the assignment is in
    aid: The object ID of the assignment group to add the problem to

  Forms Handled: None
  '''
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))


    a = AssignmentGroup.objects.get(id=aid)

    #Remove the filestorage
    removePath(getAssignmentPath(c, a))

    c.assignments.remove(a)

    c.gradeBook.assignmentGrades.remove(a.gradeEntry)

    a.gradeEntry.cleanup()
    a.gradeEntry.delete()
    a.cleanup()
    a.delete()
    c.save()
    flash("Assignment Group Removed")
  except Exception as e:
    raise e
  return redirect(url_for('administerCourse', cid=cid))

#
# Functions for adding and removing users
#

@app.route('/editcourse/<cid>/adduser', methods=['POST'])
@login_required
def addUserCourse(cid):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Add a user to the specified course. What type of user (Student,
  grutor, or instructor) is determined by the value of the submit button of the
  form.

  Inputs:
    cid: The object ID of the course to add the user to

  Forms Handled:
    AddUserCourseForm: Read in the username and determine which type of user
    based on the value of the submit button.
  '''
  try:
    c = Course.objects.get(id=cid)

    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    if request.method == "POST":
      form = AddUserCourseForm(request.form)
      if form.validate():
        u = User.objects.get(username=form.uname.data)
        if request.form['btn'] == "student":
          u.courseStudent.append(c)
        elif request.form['btn'] == "grutor":
          u.courseGrutor.append(c)
        else:
          u.courseInstructor.append(c)
        u.save()
  except User.DoesNotExist:
    flash("Failed to find user", "error")
  except Exception as e:
    raise e
  return redirect(url_for('administerCourse', cid=cid))

@app.route('/editcourse/<cid>/remuser/<uid>/<t>')
@login_required
def remUserCourse(cid, uid, t):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Remove a user of the specified type from the course.

  Inputs:
    cid: The object ID of the course to remove the user from
    uid: The object ID of the user to remove
    t: The type of user (Student, Grutor, Instructor) to remove the user from

  Forms Handled: None
  '''
  try:
    c = Course.objects.get(id=cid)

    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))


    u = User.objects.get(id=uid)
    if t == "student":
      u.courseStudent.remove(c)
    elif t == "grutor":
      u.courseGrutor.remove(c)
    else:
      u.courseInstructor.remove(c)
    u.save()

  except User.DoesNotExist:
    flash("Failed to find user")
  except Exception as e:
    raise e
  return redirect(url_for('administerCourse', cid=cid))

#
# Functions for adding and removing problems
#

@app.route('/assignment/<cid>/<aid>/addproblem')
@login_required
def addProblem(cid,aid):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Add a problem to the specified assignment in a course. When
  added it redirects to a page to edit the problem settings.

  Inputs:
    cid: The object ID of the course the assignment is in
    aid: The object ID of the assignment group to add the problem to

  Forms Handled: None
  '''
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    a = AssignmentGroup.objects.get(id=aid)

    problemNumber = len(a.problems)
    #default problem name
    problemName = "Problem " + str(problemNumber)

    p = Problem(problemName)
    p.save()

    gc = GBColumn(problemName)
    gc.save()

    p.gradeColumn = gc
    p.save()

    #Put the problem in the assignment
    a.problems.append(p)
    a.save()

    #Put the column in the gradebook
    a.gradeEntry.columns.append(gc)
    a.gradeEntry.save()

    #Create the storage space for the problem and its tests
    ensurePathExists(getProblemPath(c,a,p))
    ensurePathExists(getTestPath(c,a,p))

    flash("This is your first time creating the problem please fill in all the form fields an hit save")
    return redirect(url_for('editProblem', cid=cid, aid=a.id, pid=p.id))
  except Exception as e:
    raise e

@app.route('/assignment/<cid>/<aid>/remproblem/<pid>')
@login_required
def remProblem(cid,aid,pid):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Remove a problem from a specified assignment.

  Inputs:
    cid: The object ID of the course the assignment is in
    aid: The object ID of the assignment group to add the problem to
    pid: The object ID of the problem to remove

  Forms Handled: None
  '''
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    a = AssignmentGroup.objects.get(id=aid)
    p = Problem.objects.get(id=pid)

    #Remove storage space
    removePath(getProblemPath(c, a, p))

    #We leverage mongo's reverse delete rules to remove the problem from the
    #assignment's problem list

    p.cleanup()
    #p.gradeColumn.delete()
    #a.problems.remove(p)
    p.delete()
    #a.save()

    return redirect(url_for('administerCourse', cid=cid))
  except Course.DoesNotExist:
    pass
