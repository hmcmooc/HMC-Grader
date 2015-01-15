# coding=utf-8
'''
This module handles all functions responsible for displaying the course
statistics.

View Function: instructorCourseStats

Redirect Functions: None

AJAX Functions: TODO
'''

#Import the app
from app import app

#Import needed flask functions
from flask import g, render_template, redirect, url_for, flash, jsonify, abort
from flask import request
from flask.ext.login import current_user, login_required

#Import the models we need on these pages
from app.structures.models.user import *
from app.structures.models.gradebook import *
from app.structures.models.course import *
from app.structures.models.stats import *

from mongoengine import Q

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
      abort(403)

    uids = [str(u.id) for u in User.objects.filter(courseGrutor=c)]+\
        [str(u.id) for u in User.objects.filter(courseInstructor=c)]

    uids = list(set(uids))

    return render_template("instructor/stats.html", course = c, uids=uids)
  except Course.DoesNotExist as e:
    abort(404)

def submissionData(course, start=datetime.min, end=datetime.max):
  buckets = {}
  for d in range(7):
    for h in range(24):
      buckets[(d,h)] = 0
  for a in course.assignments:
    for p in a.problems:
      for sl in p.studentSubmissions.values():
        for s in sl.submissions:
          if s.submissionTime > start and s.submissionTime < end:
            key = (s.submissionTime.weekday(), s.submissionTime.hour)
            buckets[key] += 1

  outList = []
  for k, v in buckets.iteritems():
    outList.append([k[0], k[1], v])
  return outList

@app.route('/stats/<cid>/submissions', methods=['POST'])
@login_required
def ajaxSubmissionStats(cid):
  try:
    c = Course.objects.get(id = cid)
    if not (g.user.isAdmin or c in current_user.gradingCourses()):
      return jsonify(error="permission denied")

    import dateutil.parser
    content = request.get_json()
    startTime = dateutil.parser.parse(content['start'][:-1])
    startTime.replace(tzinfo=None)
    endTime = dateutil.parser.parse(content['end'][:-1])
    endTime.replace(tzinfo=None)

    return jsonify(data=submissionData(c, startTime, endTime), error=False)
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
        if count == 0:
          data += "<td class='danger'>"
        else:
          data += "<td>"
        data += str(count)+"</td>"

    data += "</tr>"

    return jsonify(row=data)

  except Exception as e:
    return jsonify(error=str(e))

def getTutoringSessions(time):
  from datetime import timedelta
  sMax = timedelta(minutes=20)
  eMin = timedelta(minutes=10)
  eMax = timedelta(minutes=30)

  return TutoringSession.objects((Q(startTime__gte=time) & Q(startTime__lte=time+sMax)) |
        (Q(endTime__gte=time+eMin) & Q(endTime__lte=time+eMax)))

@app.route('/stats/<cid>/tutoring', methods=['POST'])
@login_required
def ajaxTutoringStats(cid):
  try:
    c = Course.objects.get(id=cid)
    if not c in g.user.gradingCourses():
      return jsonify(error="permission denied")

    content = request.get_json()
    import dateutil.parser
    from datetime import timedelta, time, date, datetime
    startDate = dateutil.parser.parse(content['weekStart'][:-1])
    startDate.replace(tzinfo=None)
    #TODO: GENERATE COUNTS HERE AND LINKS TO DETAIL PAGES
    out = ""
    startDelta = timedelta(hours=12)
    startTime = datetime.combine(date.today(), time(hour=12))
    for h in range(24):
      out += "<tr><td>%s-%s</td>" % (startTime.strftime("%I:%M%p"), (startTime+timedelta(minutes=30)).strftime("%I:%M%p"))
      dayTime = startDate + startDelta
      for d in range(7):
        out += "<td>%d</td>" % (len(getTutoringSessions(dayTime)))
        dayTime = dayTime + timedelta(days=1)
      out += "<tr>"
      startDelta = startDelta + timedelta(minutes=30)
      startTime = startTime + timedelta(minutes=30)

    return jsonify(table=out)

  except Exception as e:
    return jsonify(error=str(e))
