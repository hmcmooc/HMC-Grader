# -*- coding: utf-8 -*-

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for, flash, send_file
from flask.ext.login import login_user, logout_user, current_user, login_required

from flask.ext.mongoengine import DoesNotExist

from werkzeug import secure_filename

from models import *
from forms import SubmitAssignmentForm

import os, datetime

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

@app.route('/grutor/gradelist/<cid>/<aid>/<pid>')
@login_required
def grutorGradelistProblem(cid, aid, pid):
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.gradingCourses()):
      return redirect(url_for('index'))

    p = Problem.objects.get(id=pid)
    a = AssignmentGroup.objects.get(id=aid)
    s = User.objects.filter(courseStudent=c)

    return render_template("grutor/problems.html", \
                            course=c, problem=p, assignment=a, users=s)
  except Exception as e:
    raise e

@app.route('/grutor/grade/<cid>/<aid>/<pid>/<subnum>')
@login_required
def grutorGradeSubmission(cid, aid, pid, subnum):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.gradingCourses()):
      return redirect(url_for('index'))

    #p = Problem.objects.get(id=pid)
    #a = AssignmentGroup.objects.get(id=aid)


    return render_template("grutor/gradesubmission.html", \
                            course=c, problem=p, assignment=a, subnum=subnum)
  except Exception as e:
    raise e

'''
Callbacks for Javascript
'''

@app.route('/grutor/grade/<pid>/<subnum>/savegrade')
@login_required
def grutorSaveGrades(cid, aid, pid, subnum):
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.gradingCourses()):
      return redirect(url_for('index'))

    p = Problem.objects.get(id=pid)
    a,c = p.getParents()
  except:
    pass
