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
