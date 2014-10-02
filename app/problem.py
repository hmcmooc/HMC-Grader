# -*- coding: utf-8 -*-

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for, flash
from flask.ext.login import login_user, logout_user, current_user, login_required

from flask.ext.mongoengine import DoesNotExist

from models import *
from forms import CreateAssignmentForm, AddUserCourseForm, ProblemOptionsForm

import traceback, StringIO, sys
import dateutil.parser

@app.route('/editcourse/<cid>/<aid>/p/<pid>')
@login_required
def editProblem(cid, aid, pid):
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    a = AssignmentGroup.objects.get(id=aid)
    p = Problem.objects.get(id=pid)

    return render_template("instructor/problem.html", course=c, problem=p, assignment=a,\
                           form=ProblemOptionsForm())
  except Exception as e:
    flash(str(e))
    return redirect(url_for('administerCourse', id=cid))

@app.route('/editcourse/<cid>/<aid>/p/<pid>/update', methods=['POST'])
@login_required
def updateProblem(cid, aid, pid):
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    p = Problem.objects.get(id=pid)

    if request.method == "POST":
      form = ProblemOptionsForm(request.form)
      if form.validate():
        p.name = form.name.data
        p.duedate = dateutil.parser.parse(form.hiddentime.data)
        p.save()
  except Exception as e:
    flash(str(e))
  return redirect(url_for('editProblem', cid=cid, aid=aid, pid=pid))

@app.route('/editcourse/<cid>/<aid>/p/<pid>/addrubricsection', methods=['POST'])
@login_required
def addRubricSec(cid, aid, pid):
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    p = Problem.objects.get(id=pid)
  except:
    pass
  return redirect(url_for('editProblem', cid=cid, aid=aid, pid=pid))
