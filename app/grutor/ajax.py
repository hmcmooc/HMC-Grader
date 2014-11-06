# -*- coding: utf-8 -*-
'''
This module supports all of the view and callback functions that can be used by
grutors and instructors performing a grutor role.
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


@app.route('/grutor/grade/<pid>/<uid>/<subnum>/savegrade', methods=['POST'])
@login_required
def grutorSaveGrades(pid, uid, subnum):
  '''
  Function Type: Callback-AJAX Function
  Called By: grutor/gradesubmission.html:saveGrades()
  Purpose: Recieves a list of grades from the page and puts them into the grade
  for this submission.

  Inputs:
    pid: The problem that this grade is for
    uid: The user whose grade this is
    subnum: The submission number that is currently being graded

  POST Values: A dictionary mapping names of rubric sections to numbers.

  Outputs:
    res: The result. True if it succeeded, False if it failed, and a string
    if there was an exception.
  '''
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()

    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.gradingCourses()):
      return jsonify(res=False)

    #Try to get the contents
    content = request.get_json()

    #make sure we got the contents
    if content == None:
      return jsonify(res=False)

    #Define function for applying scores to a submission
    def score(sub):
      for section in content:
        sub.grade.scores[section] = content[section]

      sub.grade.save()
      sub.save()
    #End definition

    user = User.objects.get(id=uid)
    sub = p.getSubmission(user, subnum)

    score(sub)
    if sub.partnerInfo != None:
      score(sub.partnerInfo.submission)

    return jsonify(res=True)

  except Exception as e:
    return jsonify(res="Exception raised: "+ str(e))

@app.route('/grutor/grade/preview', methods=['POST'])
@login_required
def grutorPreview():
  '''
  Funcion Type: Callback-AJAX Function
  Called By: grutor/gradesubmission.html:$("#previewBtn").click(...)
  Purpose: Produce HTML from a given markdown string.

  Inputs: None

  POST Values: A json object containing one field called "text" which contains
  the markdown formatted string.

  Outputs:
    res: The resulting html generated from the markdown
  '''
  content = request.get_json()
  html = markdown.markdown(content["text"])
  return jsonify(res=html)

@app.route('/grutor/grade/<pid>/<uid>/<subnum>/savecomment', methods=['POST'])
@login_required
def grutorSaveComment(pid, uid, subnum):
  '''
  Function Type: Callback-AJAX Function
  Called By: grutor/gradesubmission.html:saveComments()
  Purpose: Recieves a markdown formatted string and saves it as a grader
  comment for a specified submission

  Inputs:
    pid: The problem that this grade is for
    uid: The user whose grade this is
    subnum: The submission number that is currently being graded

  POST Values: A json object containing one field called "text" which contains
  the markdown formatted string

  Outputs:
    res: The result. True if it succeeded, False if it failed, and a string
    if there was an exception.
  '''
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()

    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.gradingCourses()):
      return jsonify(res=False)

    #Try to get the contents
    content = request.get_json()

    #make sure we got the contents
    if content == None:
      return jsonify(res=False)

    #Define function for saving comments
    def comment(sub):
      sub.comments = content['text']
      sub.save()

    user = User.objects.get(id=uid)
    sub = p.getSubmission(user, subnum)

    comment(sub)
    if sub.partnerInfo != None:
      comment(sub.partnerInfo.submission)


    #Save changes to the problem
    p.save(cascade=True)

    return jsonify(res=True)

  except Exception as e:
    return jsonify(res="Exception raised: "+ str(e))

@app.route('/gradebook/<cid>/<col>/save', methods=['POST'])
@login_required
def saveGradeColumn(cid,col):
  try:
    course = Course.objects.get(id=cid)
    column = GBColumn.objects.get(id=col)

    if not (course in current_user.gradingCourses() or current_user.isAdmin):
      return jsonify(res=False)

    content = request.get_json()

    column.maxScore = content['maxScore']

    for id in content['scores']:
      u = User.objects.get(id=id)
      column.scores[u.username].scores['score'] = content['scores'][id]
      column.scores[u.username].save()

    column.save()

    return jsonify(res=True)

  except Exception as e:
    return jsonify(res=False, exeption=str(e))
