# -*- coding: utf-8 -*-

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for, flash, send_file, jsonify
from flask.ext.login import login_user, logout_user, current_user, login_required

from flask.ext.mongoengine import DoesNotExist

from werkzeug import secure_filename

from models import *
from forms import SubmitAssignmentForm

import os, datetime
import markdown

@app.route('/grutor/assignments/<cid>')
@login_required
def grutorAssignments(cid):
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.gradingCourses()):
      return redirect(url_for('index'))

    return render_template("grutor/assignments.html", course=c)
  except Exception as e:
    raise e

@app.route('/grutor/gradelist/problem/<pid>')
@login_required
def grutorGradelistProblem(pid):
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

    p.save()

    return render_template("grutor/gradesubmission.html", \
                            course=c, problem=p, assignment=a, subnum=subnum,
                            user=user, submission=submission)
  except Exception as e:
    raise e


@app.route('/grutor/finish/<pid>/<uid>/<subnum>')
@login_required
def grutorFinishSubmission(pid, uid, subnum):
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
    submission.status = max(submission.status, 4)

    for g in submission.grade.scores:
      submission.grade.visible[g] = True

    submission.grade.save()

    p.save()

    return redirect(url_for('grutorGradelistProblem', pid=pid))
  except Exception as e:
    raise e

@app.route('/grutor/release/<pid>/<uid>/<subnum>')
@login_required
def grutorReleaseSubmission(pid, uid, subnum):
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
    #if not submission.status == 4:
    submission.status = min(submission.status, 2)

    submission.grade.save()

    p.save()

    return redirect(url_for('grutorGradelistProblem', pid=pid))
  except Exception as e:
    raise e

'''
Function to create a blank submission
'''

@app.route('/grutor/create/<pid>/<uid>')
@login_required
def grutorMakeBlank(pid, uid):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    user = User.objects.get(id=uid)

    #For security purposes we send anyone who isnt in this class to the index
    if not (c in current_user.gradingCourses()):
      return redirect(url_for('index'))

    #Check that the user we are trying to create a submission for is in the class
    if not (c in user.courseStudent):
      return redirect(url_for('index'))
  except:
    pass



'''
Callbacks for Javascript
'''

@app.route('/grutor/grade/<pid>/<uid>/<subnum>/savegrade', methods=['POST'])
@login_required
def grutorSaveGrades(pid, uid, subnum):
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

    user = User.objects.get(id=uid)
    sub = p.getSubmission(user, subnum)

    #put the sections in the grade
    for section in content:
      sub.grade.scores[section] = content[section]

    #Save changes to the problem
    p.save(cascade=True)
    sub.grade.save()

    return jsonify(res=True)

  except Exception as e:
    return jsonify(res="Exception raised: "+ str(e))

@app.route('/grutor/grade/preview', methods=['POST'])
@login_required
def grutorPreview():
  content = request.get_json()
  html = markdown.markdown(content["text"])
  return jsonify(res=html)

@app.route('/grutor/grade/<pid>/<uid>/<subnum>/savecomment', methods=['POST'])
@login_required
def grutorSaveComment(pid, uid, subnum):
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

    user = User.objects.get(id=uid)
    sub = p.getSubmission(user, subnum)

    #put the sections in the grade
    sub.comments = content["text"]


    #Save changes to the problem
    p.save(cascade=True)

    return jsonify(res=True)

  except Exception as e:
    return jsonify(res="Exception raised: "+ str(e))
