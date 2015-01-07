# -*- coding: utf-8 -*-
'''
This module supports all of the view and callback functions that can be used by
grutors and instructors performing a grutor role.
'''

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for, flash, send_file, jsonify, abort
from flask.ext.login import login_user, logout_user, current_user, login_required

from flask.ext.mongoengine import DoesNotExist

from werkzeug import secure_filename

from app.structures.models.user import *
from app.structures.models.gradebook import *
from app.structures.models.course import *

from app.structures.forms import SubmitAssignmentForm

import os, datetime, fcntl, random
import markdown

def grutorSubArchive(p, c, a, user, sub):
  _, subnum = p.getSubmissionInfo(sub)
  with open(os.path.join(getSubmissionPath(c,a,p,user,subnum), '.gradeArchive'), 'w') as f:
    f.write("#Scores#\n")
    for sec, score in sub.grade.scores.iteritems():
      f.write(sec+":"+str(score)+"\n")
    f.write("\n#info#\n")
    f.write("isLate:" + str(sub.isLate)+"\n")
    if sub.partner == None:
      f.write("partner: None\n")
    else:
      f.write("partner: " + sub.partner.username + "\n")
    if sub.gradedBy != None: #This should always be true
      f.write("gradedBy: " + sub.gradedBy.username + "\n")
    f.write('\n')
    f.write(sub.comments)

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
    grutorSubArchive(p, c, a, user, sub)
    if sub.partner != None:
      score(sub.partnerSubmission)
      grutorSubArchive(p, c, a, sub.partner, sub.partnerSubmission)

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
  autohtml = markdown.markdown(content['autotext'])
  return jsonify(res=html, autores=autohtml)

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
      sub.autoGraderComments = content['autotext']
      sub.save()

    user = User.objects.get(id=uid)
    sub = p.getSubmission(user, subnum)

    comment(sub)

    grutorSubArchive(p, c, a, user, sub)
    if sub.partner != None:
      comment(sub.partnerSubmission)
      grutorSubArchive(p, c, a, sub.partner, sub.partnerSubmission)


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


@app.route('/grutor/toggleLate/<pid>/<uid>/<subnum>')
@login_required
def grutorToggleLate(pid, uid, subnum):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Toggle the isLate flag for an assignment

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
      return jsonify(res=False)

    #Define function for releasing submissions
    def toggle(sub):
      sub.isLate = not sub.isLate
      sub.save()
    #End definition

    submission = p.getSubmission(user, subnum)
    #if not submission.status == 4:
    toggle(submission)

    if submission.partner != None:
      toggle(submission.partnerSubmission)

    p.save()

    return jsonify(res=True)
  except (Problem.DoesNotExist, Course.DoesNotExist, AssignmentGroup.DoesNotExist):
    pass
  return jsonify(res=False)
