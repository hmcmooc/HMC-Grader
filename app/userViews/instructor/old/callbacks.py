# -*- coding: utf-8 -*-

'''
This module supports operations for instructors to manage courses and assignments
'''

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for, flash, jsonify
from flask.ext.login import login_user, logout_user, current_user, login_required

from flask.ext.mongoengine import DoesNotExist

from app.models.user import *
from app.models.gradebook import *
from app.models.course import *

from app.forms import CreateAssignmentForm, AddUserCourseForm, ProblemOptionsForm, CourseSettingsForm
from app.forms import CreateGradebookGroupForm, CreateGradeColumnForm
from app.helpers.filestorage import ensurePathExists, getAssignmentPath, removePath, getProblemPath, getTestPath

import traceback, StringIO, sys
import dateutil.parser




@app.route('/gradebook/<cid>/addGroup', methods=['POST'])
@login_required
def addGradeGroup(cid):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Add a grade group to the gradebook for a course

  Inputs:
    cid: The object ID of the course to modify

  Forms Handled:
    CreateGradebookGroupForm: Reads in the name and creates that group if it
    doesn't already exist
  '''
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    grades = c.gradeBook.auxillaryGrades

    if request.method == 'POST':
      form = CreateGradebookGroupForm(request.form)
      if form.validate():
        for grade in grades:
          if grade.name == form.groupName.data:
            flash("Group name already exists")
            return redirect(url_for('viewGradebook', cid=cid))

        group = GBGroup(form.groupName.data)
        group.save()
        c.gradeBook.auxillaryGrades.append(group)
        c.save()
        flash("Added group")
    return redirect(url_for('viewGradebook', cid=cid))
  except Exception as e:
    raise e

@app.route('/gradebook/<cid>/addColumn', methods=['POST'])
@login_required
def addGradeColumn(cid):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Add a grade group to the gradebook for a course

  Inputs:
    cid: The object ID of the course to modify

  Forms Handled:
    CreateGradebookGroupForm: Reads in the name and creates that group if it
    doesn't already exist
  '''
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    if request.method == 'POST':
      form = CreateGradeColumnForm(request.form)
      form.group.choices = [(unicode(x.id),x.name) for x in c.gradeBook.auxillaryGrades]

      if form.validate():
        group = GBGroup.objects.get(id=form.group.data)
        for c in group.columns:
          if c.name == form.name.data:
            flash("Column name already exists", "warning")
            return redirect(url_for('viewGradebook', cid=cid))

        col = GBColumn(form.name.data)
        col.save()
        group.columns.append(col)
        group.save()
        flash("Group added")
    return redirect(url_for('viewGradebook', cid=cid))
  except Exception as e:
    raise e

#
# Gradebook redirect function
#

@app.route('/gradebook/<cid>/edit/<col>/<instr>')
@login_required
def redirectGradebook(cid, col, instr):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Given a gradebook column redirect to either the problem editing page
  or the column editing page depening on if the column is for a problem or just
  an arbitrary grade

  Inputs:
    cid: The object ID for the course that this column is in
    col: The object ID of the GBColumn that we are trying to redirect to

  Forms Handled: None
  '''
  c = Course.objects.get(id=cid)
  col = GBColumn.objects.get(id=col)
  for a in c.assignments:
    for p in a.problems:
      if p.gradeColumn == col:
        return redirect(url_for('grutorGradelistProblem', pid=p.id))
  if instr == "true":
    return redirect(url_for('editGradebook', cid=c.id, col=col.id))
  else:
    return redirect(url_for('grutorEditGradebook', cid=c.id, col=col.id))
