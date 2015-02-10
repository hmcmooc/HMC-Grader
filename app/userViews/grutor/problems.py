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

@app.route('/grutor/grade/<pid>/status')
@login_required
def grutorGetStatus(pid):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()

    if not (c in current_user.gradingCourses()):
      abort(403)

    u, i, d = p.getStatusCount()

    return jsonify(u=u, i=i, d=d)
  except Problem.DoesNotExist:
    abort(404)
