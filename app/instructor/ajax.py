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
from decimal import Decimal

@app.route('/assignment/<cid>/settings', methods=['POST'])
@login_required
def instructorSaveSettings(cid):
  '''
  Function Type: Callback-AJAX Function
  Called By: instructor/course.html:saveSettings()
  Purpose: Recieves the current state of the settings form and applies those
  settings to the course.

  Inputs:
    cid: The object ID of the course to apply the settings to

  POST Values: A dictionary of settings names to values

  Outputs:
    res: True if the operation succeeded otherwise False
  '''
  try:
    c = Course.objects.get(id=cid)
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return jsonify(res=False)

    content = request.get_json()
    c.anonymousGrading = content['anonymousGrading']
    c.lateGradePolicy = content['lateGradePolicy']
    c.save()
    return jsonify(res=True)
  except:
    return jsonify(res=False)

def preventCollapse(gradeList):
  for a in gradeList:
    if len(a) == 0:
      a.append(None)
  return gradeList

def processGradelist(gradeList, lateCalculator):
  gl = lateCalculator(gradeList)
  gl = preventCollapse(gl)
  gl = list(itertools.chain.from_iterable(gl))
  return gl

def createHighlight(d):
  if 'highlight' in d:
    if d['highlight'] == 'red':
      return "class='danger'"
    elif d['highlight'] == 'yellow':
      return "class='warning'"
    elif d['highlight'] == 'blue':
      return "class='info'"
    elif d['highlight'] == 'green':
      return "class='success'"
  else:
    return ""

@app.route('/grades/<cid>/render', methods=['POST'])
@login_required
def ajaxRenderGrade(cid):
  '''
  Function Type: Callback-AJAX Function
  Called By: instructor/gradebook.html:renderGrades()
  Purpose: Render one row of the gradebook asynchronously for to allow the page
  to load quickly.

  Inputs:
    cid: The object ID of the course to render the grades for
    uid: The object ID of the user to render the grades for

  Outputs:
    res: An HTML string containing one <tr>...</tr>
  '''
  try:
    c = Course.objects.get(id=cid)
    content = request.get_json()
    u = User.objects.get(id=content['uid'])
    if not (g.user.isAdmin or c in current_user.courseInstructor or u == g.user):
      return jsonify(res="<tr><td>Permission Denied</td></tr>")

    outstring = "<tr>"

    outstring += "<td>"+u.username+"</td>"

    # Create a gradelist
    gl = []
    for a in c.assignments:
      al = []
      for p in a.problems:
        sub = p.getLatestSubmission(u)
        if not sub == None:
          gradeData = {}
          gradeData['rawTotalScore'] = sub.grade.totalScore()
          gradeData['timeDelta'] = p.duedate - sub.submissionTime
          gradeData['isLate'] = sub.isLate
          gradeData['maxScore'] = p.totalPoints()
          al.append(gradeData)
        else:
          al.append(None)
      gl.append(al)

    #Calculate the late score adjustment
    lateCalculator = getLateCalculators()[c.lateGradePolicy]
    gl = processGradelist(gl, lateCalculator)

    courseScore = Decimal('0.00')
    userScore = Decimal('0.00')

    for i, col in enumerate(c.gradeBook.columns()):
      if col == None:
        outstring += "<td class='active'></td>"
      else:
        courseScore += col.maxScore

        #Check if we are still in a submission grade column
        if i < len(gl):
          if gl[i] != None:
            outstring += "<td " + createHighlight(gl[i]) + ">"
            if 'finalTotalScore' in gl[i]:
              userScore += gl[i]['finalTotalScore']
              outstring += str(gl[i]['finalTotalScore'])
            else:
              userScore += gl[i]['rawTotalScore']
              outstring += str(gl[i]['rawTotalScore'])
            outstring += "/"+str(col.maxScore)
            outstring += "</td>"
          else:
            outstring += "<td>0.00/"+str(col.maxScore)+"</td>"
        else:
          #We are in an arbitrary column
          outstring += "<td>"
          if u.username in col.scores:
            grade = col.scores[u.username]
            userScore += grade.totalScore()
            outstring += str(g.totalScore())
          else:
            outstring += "0.00"
          outstring += "/"+str(col.maxScore)+"</td>"

    outstring += "<td>"+str(userScore)+"/"+str(courseScore)+"</td>"
    outstring += "</tr>"

    return jsonify(res=outstring)

  except Exception as e:
    return jsonify(res="<tr><td>"+str(e)+"</td></tr>")
