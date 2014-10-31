# -*- coding: utf-8 -*-

'''
This module supports operations for instructors to manage courses and assignments
'''

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for, flash, jsonify
from flask.ext.login import login_user, logout_user, current_user, login_required

from flask.ext.mongoengine import DoesNotExist

from app.models import *
from app.forms import CreateAssignmentForm, AddUserCourseForm, ProblemOptionsForm, CourseSettingsForm

import traceback, StringIO, sys
import dateutil.parser

@app.route('/assignment/<cid>/settings', methods=['POST'])
@login_required
def instructorSaveSettings(cid):
  '''
  Function Type: Callback-AJAX Function
  Called By: instructor/course.html:saveSettings()
  Purpose: Recieves the current state of the settings form and applies those
  settings to the course.

  Inputs:
    cid: The object ID of the course to apply the settings to

  POST Values: A dictionary of settings names to values

  Outputs:
    res: True if the operation succeeded otherwise False
  '''
  try:
    c = Course.objects.get(id=cid)
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return jsonify(res=False)

    content = request.get_json()
    c.anonymousGrading = content['anonymousGrading']
    c.save()
    return jsonify(res=True)
  except:
    return jsonify(res=False)
