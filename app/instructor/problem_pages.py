# -*- coding: utf-8 -*-

#import the app
from app import app

from flask import g, request, render_template, redirect, url_for, flash, abort
from flask.ext.login import current_user, login_required

from app.models.course import *
from app.models.gradenotes import *

from app.forms import ProblemOptionsForm, AddTestForm

from werkzeug import secure_filename

@app.route('/instructor/makepage/<pid>/<type>')
@login_required
def makeNewPage(pid, type):
  try:
    p = Problem.objects.get(id=pid)
    c, a = Problem.getParents()

    if not  c in current_user.courseInstructor:
      abort(403)

    notes = GradeNotes()

  except Problem.DoesNotExist:
    abort(404)
