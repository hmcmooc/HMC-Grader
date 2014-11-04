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
from app.latework import getLateCalculators

import traceback, StringIO, sys
import dateutil.parser, itertools

def createGradeLists(users, course):
  gradeLists = {}
  for u in users:
    gl = []
    for a in course.assignments:
      al = []
      for p in a.problems:
        sub = p.getLatestSubmission(u)
        if not sub == None:
          gradeData = {}
          gradeData['rawTotalScore'] = sub.grade.totalScore()
          gradeData['timeDelta'] = p.duedate - sub.submissionTime
          gradeData['isLate'] = sub.isLate
          al.append(gradeData)
        else:
          al.append(None)
      if len(al) == 0:
        al.append(None)
      gl.append(al)
    gradeLists[u.username] = gl
  return gradeLists

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

    #TODO: Refactor user forms to use javascript/AJAX
    return render_template("instructor/course.html",\
     course=c, students=s, grutors=grutor, instrs=i,\
     form=CreateAssignmentForm(), suserform=AddUserCourseForm(),\
     guserform=AddUserCourseForm(), iuserform=AddUserCourseForm(),
     settingsForm=settingsForm)
  except Course.DoesNotExist:
    return redirect(url_for('index'))

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
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    #Get the users for this course
    s = User.objects.filter(courseStudent=c)

    gradeLists = createGradeLists(s, c)

    #perform late calculation
    lateCalculator = getLateCalculators()[c.lateGradePolicy]
    #Apply calculator
    gradeLists = dict(map(lambda (k,v): (k, lateCalculator(v)), gradeLists.iteritems()))
    #Flatten lists
    gradeLists = dict(map(lambda (k,v): (k, list(itertools.chain.from_iterable(v))), gradeLists.iteritems()))

    return render_template('instructor/gradebook.html', course=c, students=s,\
                          gradeLists=gradeLists)
  except Course.DoesNotExist:
    pass
