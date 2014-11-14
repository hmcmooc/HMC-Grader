# -*- coding: utf-8 -*-

#import the app
from app import app

from flask import g, request, render_template, redirect, url_for, flash, abort
from flask.ext.login import current_user, login_required

from app.models.course import *
from app.models.pages import *

from app.forms import ProblemOptionsForm, AddTestForm

from werkzeug import secure_filename

@app.route('/instructor/makepage/<pid>/<t>')
@login_required
def makeProblemNewPage(pid, t):
  try:
    p = Problem.objects.get(id=pid)
    c, a = Problem.getParents()

    if not  c in current_user.courseInstructor:
      abort(403)

    notes = Page()
    notes.save()

    if t == "notes":
      p.gradeNotes = url_for('viewPage', pgid=notes.id)
    else:
      p.problemPage = url_for('viewPage', pgid=notes.id)


    return redirect(url_for('editPage', notes.id))
  except Problem.DoesNotExist:
    abort(404)

@app.route('/viewpage/<pgid>')
@login_required
def viewPage(pgid):
  return redirect(url_for('index'))


@app.route('/editpage/<pgid>')
@login_required
def editPage(pgid):
  return rediret(url_for('index'))
