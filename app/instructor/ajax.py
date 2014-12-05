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
from app.latework import getLateCalculators


import traceback, StringIO, sys
import dateutil.parser, itertools
from decimal import Decimal

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

def getProblem(course, col):
  for a in course.assignments:
    for p in a.problems:
      if p.gradeColumn == col:
        return p

@app.route('/rendergrades', methods=['POST'])
@login_required
def ajaxRenderGrade():
  '''
  Function Type: Callback-AJAX Function
  Called By: instructor/gradebook.html:$(), student/viewgrades.html:$()
  Purpose: Render one row of the gradebook asynchronously for to allow the page
  to load quickly.

  Inputs:
    cid: The object ID of the course to render the grades for
    uid: The object ID of the user to render the grades for

  Outputs:
    res: An HTML string containing one <tr>...</tr>
  '''
  try:
    content = request.get_json()
    c = Course.objects.get(id=content['cid'])
    u = User.objects.get(id=content['uid'])
    if not (g.user.isAdmin or c in current_user.gradingCourses() or u.id == current_user.id):
      return jsonify(res="<tr><td>Permission Denied</td></tr>", cid=content['cid'])

    outstring = "<tr>"

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
          p = getProblem(c, col)
          if gl[i] != None:
            outstring += "<td " + createHighlight(gl[i]) + ">"
            if content['links']:
              outstring += "<a href='"
              outstring += url_for('grutorGradeSubmission', pid=p.id, uid=u.id, subnum=p.getSubmissionNumber(u))
              outstring += "'>"

            if 'finalTotalScore' in gl[i]:
              userScore += gl[i]['finalTotalScore']
              outstring += str(gl[i]['finalTotalScore'])
            else:
              userScore += gl[i]['rawTotalScore']
              outstring += str(gl[i]['rawTotalScore'])
            outstring += "/"+str(col.maxScore)
            outstring += "</a></td>"
          else:
            outstring += "<td class='active'>"
            if content['links']:
              outstring += "<a href='"
              outstring += url_for('grutorMakeBlank', pid=p.id, uid=u.id)
              outstring += "'>"

            outstring += "0.00/"+str(col.maxScore)+"</a></td>"
        else:
          #We are in an arbitrary column
          outstring += "<td>"
          if u.username in col.scores:
            grade = col.scores[u.username]
            userScore += grade.totalScore()
            outstring += str(grade.totalScore())
          else:
            outstring += "0.00"
          outstring += "/"+str(col.maxScore)+"</td>"

    outstring += "<td>"+str(userScore)+"/"+str(courseScore)+"</td>"
    outstring += "</tr>"

    if c.anonymousGrading:
      return jsonify(res=outstring, username=u.username,\
       cid=content['cid'], id=c.getIdentifier(u.username))
    else:
      return jsonify(res=outstring, username=u.username, cid=content['cid'])

  except Exception as e:
    import traceback
    tb = traceback.format_exc()
    return jsonify(res="<tr><td>"+str(e)+"</td><td>"+tb+"</td></tr>")

@app.route('/stats/<cid>/submissions', methods=['POST'])
@login_required
def ajaxSubmissionStats(cid):
  try:
    c = Course.objects.get(id = cid)
    if not (g.user.isAdmin or c in current_user.gradingCourses()):
      return jsonify(error="permission denied")

    from helpers import submissionData
    import dateutil.parser
    content = request.get_json()
    startTime = dateutil.parser.parse(content['start'][:-1])
    startTime.replace(tzinfo=None)
    endTime = dateutil.parser.parse(content['end'][:-1])
    endTime.replace(tzinfo=None)

    return jsonify(data=submissionData(c, startTime, endTime), error=False)
  except Exception as e:
    return jsonify(error=str(e))

@app.route('/stats/<cid>/attendance', methods=['POST'])
@login_required
def ajaxAttendanceStats(cid):
  try:
    c = Course.objects.get(id = cid)
    if not (g.user.isAdmin or c in current_user.gradingCourses()):
      return jsonify(error="permission denied")

    from helpers import attendanceData
    import dateutil.parser
    content = request.get_json()
    startTime = dateutil.parser.parse(content['start'][:-1])
    startTime.replace(tzinfo=None)
    endTime = dateutil.parser.parse(content['end'][:-1])
    endTime.replace(tzinfo=None)

    return jsonify(data=attendanceData(c, startTime, endTime), error=False)
  except Exception as e:
    return jsonify(error=str(e))


@app.route('/stats/<cid>/graderPerformance', methods=['POST'])
@login_required
def ajaxGraderPerformance(cid):
  try:
    c = Course.objects.get(id = cid)
    if not (g.user.isAdmin or c in current_user.gradingCourses()):
      return jsonify(error="permission denied")

    contents = request.get_json()

    user = User.objects.get(id=contents['uid'])

    data = "<tr>"
    data += "<td>"+user.username+"</td>"

    for a in c.assignments:
      if len(a.problems) == 0: data += "<td>N/A</td>"
      for p in a.problems:
        count = 0
        for sl in p.studentSubmissions.items():
          if sl[-1].submissions[-1].gradedBy == user:
            count += 1
        data += "<td>"+str(count)+"</td>"

    data += "</tr>"

    return jsonify(row=data)

  except Exception as e:
    return jsonify(error=str(e))
