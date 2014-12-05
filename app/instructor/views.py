# -*- coding: utf-8 -*-

'''
This module supports operations for instructors to manage courses and assignments
'''

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for, flash, jsonify
from flask.ext.login import login_user, logout_user, current_user, login_required

from flask.ext.mongoengine import DoesNotExist

from app.models.user import *
from app.models.gradebook import *
from app.models.course import *

from app.forms import CreateAssignmentForm, AddUserCourseForm, ProblemOptionsForm, CourseSettingsForm
from app.forms import CreateGradebookGroupForm, CreateGradeColumnForm
from app.latework import getLateCalculators

import traceback, StringIO, sys
import dateutil.parser, itertools
from decimal import Decimal

@app.route('/editcourse/<cid>')
@login_required
def administerCourse(cid):
  '''
  Function Type: View Function
  Template: instructor/course.html
  Purpose: Allows an instructor to manipulate the assignemnts of a course.
  Course settings, and the users and graders for a course.

  Inputs:
    cid: The object ID of the course being administered

  Template Parameters:
    course: The course specified by <cid> to be administered
    students: A list of user objects who are enrolled as students
    grutors: A list of user objects who are enrolled as grutors
    instrs: A list of user objects who are enrolled as instructorSaveSettings
    guserform: An AddUserCourseForm for adding grutors
    suserform: An AddUserCourseForm for adding students
    iuserform: An AddUserCourseForm for adding instructors
    settingsForm: A CourseSettingsForm for changing the settings of the course

  Forms Handled: None
  '''
  try:
    c = Course.objects.get(id=cid)
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    #Get the users for this course
    s = User.objects.filter(courseStudent=c)
    grutor = User.objects.filter(courseGrutor=c)
    i = User.objects.filter(courseInstructor=c)

    settingsForm = CourseSettingsForm()

    lateCalculators = getLateCalculators()

    settingsForm.latePolicy.choices = [(x,x) for x in lateCalculators.keys()]

    #Make sure all users have anonIds
    if c.anonymousGrading:
      c.ensureIDs()

    #TODO: Refactor user forms to use javascript/AJAX
    return render_template("instructor/course.html",\
     course=c, students=s, grutors=grutor, instrs=i,\
     form=CreateAssignmentForm(), suserform=AddUserCourseForm(),\
     guserform=AddUserCourseForm(), iuserform=AddUserCourseForm(),
     settingsForm=settingsForm)
  except Course.DoesNotExist:
    return redirect(url_for('index'))

# def createGradeLists(users, course):
#   gradeLists = {}
#   for u in users:
#     gl = []
#     for a in course.assignments:
#       al = []
#       for p in a.problems:
#         sub = p.getLatestSubmission(u)
#         if not sub == None:
#           gradeData = {}
#           gradeData['rawTotalScore'] = sub.grade.totalScore()
#           gradeData['timeDelta'] = p.duedate - sub.submissionTime
#           gradeData['isLate'] = sub.isLate
#           gradeData['maxScore'] = p.totalPoints()
#           al.append(gradeData)
#         else:
#           al.append(None)
#       gl.append(al)
#     gradeLists[u.username] = gl
#   return gradeLists
#
# def preventCollapse(gradeList):
#   for a in gradeList:
#     if len(a) == 0:
#       a.append(None)
#   return gradeList
#
# def processGradelist(gradeList, lateCalculator):
#   gl = lateCalculator(gradeList)
#   gl = preventCollapse(gl)
#   gl = list(itertools.chain.from_iterable(gl))
#   return gl

@app.route('/gradebook/<cid>')
@login_required
def viewGradebook(cid):
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
      return redirect(url_for('index'))

    #Get the users for this course
    s = User.objects.filter(courseStudent=c)


    disableColForm = False
    colForm = CreateGradeColumnForm()
    colForm.group.choices = [(x.id,x.name) for x in c.gradeBook.auxillaryGrades]
    if len(colForm.group.choices) == 0:
      colForm.group.choices = [("N/A", "N/A")]
      disableColForm = True


    s = list(s)
    s.sort(key=lambda x:x.username)
    uids = [str(u.id) for u in s]

    return render_template('instructor/gradebook.html', course=c, uids=uids,\
                      groupForm=CreateGradebookGroupForm(),\
                      colForm=colForm, disableColForm=disableColForm)
  except Course.DoesNotExist:
    pass

@app.route('/gradebook/<cid>/<col>')
@login_required
def editGradebook(cid, col):
  '''
  Function Type: View Function
  Template: instructor/editcolumn.html
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
      return redirect(url_for('index'))

    users = User.objects.filter(courseStudent=course)

    for u in users:
      if not u.username in column.scores:
        flash("Creating")
        grade = GBGrade()
        grade.scores['score'] = 0
        grade.save()
        column.scores[u.username] = grade

    column.save()

    return render_template("instructor/editcolumn.html", course = course, col=column, users=users)
  except Exception as e:
    raise e

@app.route('/stats/<cid>')
@login_required
def viewCourseStats(cid):
  '''
  Function Type: View Function
  Template: instructor/stats.html
  Purpose:Display statistics about submission grader attendance and student use
  of tutoring hours

  Inputs:
    cid: The object ID for the course being viewed

  Template Parameters: TODO
  '''

  try:
    c = Course.objects.get(id=cid)

    if not(c in current_user.gradingCourses() or current_user.isAdmin):
      return redirect(url_for('index'))

    uids = [str(u.id) for u in User.objects.filter(courseGrutor=c)]+\
        [str(u.id) for u in User.objects.filter(courseInstructor=c)]

    uids = list(set(uids))

    return render_template("instructor/stats.html", course = c, uids=uids)
  except Course.DoesNotExist as e:
    raise e
