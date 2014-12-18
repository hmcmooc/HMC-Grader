# coding=utf-8

'''This module handles all functions responsible for modifying the course
settings page.

View Function: instructorProblemSettings (instructor/problemSettings.html)

Redirect Functions: TODO

AJAX Fuctions: TODO
'''

#Import the app
from app import app

#Import needed flask functions
from flask import g, render_template, redirect, url_for, flash, jsonify, abort
from flask.ext.login import current_user, login_required

#Import the models we need on these pages
from app.structures.models.user import *
from app.structures.models.gradebook import *
from app.structures.models.course import *

#Import the forms needed on these pages
from app.structures.forms import CreateAssignmentForm, AddUserCourseForm
from app.structures.forms import CourseSettingsForm

@app.route('/editproblem/<pid>')
@login_required
def editProblemSettings(pid):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    testFiles = []
    filepath = getTestPath(c, a, p)
    for f in p.testfiles:
      testFiles.append(getTestInfo(os.path.join(filepath,f)))

    testForm = AddTestForm()
    testFileParsers = getTestFileParsers()
    testForm.testType.choices = [(x,x) for x in testFileParsers.keys()]

    return render_template("instructor/problem.html", course=c, problem=p, assignment=a,\
                           form=ProblemOptionsForm(), testForm=testForm,\
                           testFiles=testFiles)
  except Exception as e:
    flash(str(e))
    return redirect(url_for('administerCourse', cid=c.id))
