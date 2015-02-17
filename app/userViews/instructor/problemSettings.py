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
from flask import request
from flask.ext.login import current_user, login_required

#Import the models we need on these pages
from app.structures.models.user import *
from app.structures.models.gradebook import *
from app.structures.models.course import *

#Import the forms needed on these pages
from app.structures.forms import AddTestForm, ProblemOptionsForm

#Import app helpers
from app.plugins.autograder import getTestFileParsers

#Generic pyhton imports
from werkzeug import secure_filename
import json
from decimal import Decimal
import dateutil

@app.route('/editproblem/<pid>')
@login_required
def instructorProblemSettings(pid):
  '''
  Function Type: View Function
  Template: instructor/problemSettings.html
  Purpose: Allows an instructor to edit the settings for a problem in a course.

  Inputs:
    pid: THe object ID of the problem to be modified

  Template Parameters:
    course: The course object for this problem
    assignment: The assignment group object for this problem
    problem: This problesm object
    form: A form for the options of this problem
    testForm: A form for creating new tests.
    testFiles: A list of filenames for existing tests
  '''
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not c in current_user.courseInstructor:
      abort(403)

    testFiles = []
    filepath = getTestPath(c, a, p)
    for f in p.testfiles:
      testFiles.append(getTestInfo(os.path.join(filepath,f)))

    testForm = AddTestForm()
    testFileParsers = getTestFileParsers()
    testForm.testType.choices = [(x,x) for x in testFileParsers.keys()]

    return render_template("instructor/problemSettings.html", course=c, problem=p, assignment=a,\
                           form=ProblemOptionsForm(), testForm=testForm,\
                           testFiles=testFiles)
  except (Problem.DoesNotExist, Course.DoesNotExist, AssignmentGroup.DoesNotExist):
    abort(404)

@app.route('/editproblem/<pid>/update', methods=['POST'])
@login_required
def instructorSaveProblemSettings(pid):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not c in current_user.courseInstructor:
      abort(403)


    if request.method == "POST":
      form = ProblemOptionsForm(request.form)
      if form.validate():
        if p.name != form.name.data:
          #We must move the path to accomodate the change
          moveProblemPath(c,a,p, form.name.data)
        p.name = form.name.data
        p.gradeColumn.name = form.name.data
        p.gradeColumn.save()
        p.duedate = dateutil.parser.parse(form.hiddentime.data)
        p.allowPartners = form.allowPartners.data
        p.releaseAutoComments = form.releaseAutoComments.data
        p.autoGradeOnly = form.autoGradeOnly.data
        p.isOpen = form.isOpen.data

        #Assign gradenotes
        if len(form.gradeNotes.data) > 0:
          p.gradeNotes = form.gradeNotes.data
        else:
          p.gradeNotes = None

        if len(form.problemPage.data) > 0:
          p.problemPage = form.problemPage.data
        else:
          p.problemPage = None

        if len(form.requiredFiles.data) > 0:
          p.requiredFiles = form.requiredFiles.data
        else:
          p.requiredFiles = None

        if len(form.strictFiles.data) > 0:
          p.strictFiles = form.strictFiles.data
        else:
          p.strictFiles = None

        p.save()

  except (Course.DoesNotExist, Problem.DoesNotExist, AssignmentGroup.DoesNotExist):
    abort(404)
  return redirect(url_for('instructorProblemSettings', pid=pid))

@app.route('/instructor/makepage/<pid>/<t>')
@login_required
def instructorMakeProblemPage(pid, t):
  try:
    p = Problem.objects.get(id=pid)
    c, a = p.getParents()

    if not  c in current_user.courseInstructor:
      abort(403)

    notes = Page()
    notes.initializePerms()
    notes.course = c
    notes.save()

    if t == "notes":
      p.gradeNotes = url_for('viewPage', pgid=notes.id)
    else:
      p.problemPage = url_for('viewPage', pgid=notes.id)

    p.save()

    return redirect(url_for('editPage', pgid=notes.id))
  except Problem.DoesNotExist:
    abort(404)

#
# Functions for manipulating the rubric
#

@app.route('/editproblem/<pid>/addrubricsection', methods=['GET'])
@login_required
def addRubricSec(pid):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not c in current_user.courseInstructor:
      abort(403)

    p.rubric[request.args['name']] = Decimal(request.args['points'])

    #update the column score in the gradebook
    p.gradeColumn.maxScore = p.totalPoints()
    p.gradeColumn.save()

    p.save()
  except (Course.DoesNotExist, Problem.DoesNotExist, AssignmentGroup.DoesNotExist):
    abort(404)
  return redirect(url_for('instructorProblemSettings', pid=pid))

@app.route('/editproblem/<pid>/delrubricsection/<name>', methods=['GET'])
@login_required
def delRubricSec(pid, name):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not c in current_user.courseInstructor:
      abort(403)

    del p.rubric[name]

    #update the column score in the gradebook
    p.gradeColumn.maxScore = p.totalPoints()
    p.gradeColumn.save()

    p.save()
  except (Course.DoesNotExist, Problem.DoesNotExist, AssignmentGroup.DoesNotExist):
    abort(404)
  return redirect(url_for('instructorProblemSettings', pid=pid))

#
# Functions for modifying the tests on this page
#

@app.route('/editproblem/<pid>/addTestFile', methods=['POST'])
@login_required
def addTestFile(pid):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not c in current_user.courseInstructor:
      abort(403)

    if request.method == "POST":
      form = AddTestForm(request.form)

      testFileParsers = getTestFileParsers()
      form.testType.choices = [(x,x) for x in testFileParsers.keys()]
      if form.validate():
        filepath = getTestPath(c, a, p)

        if not os.path.isdir(filepath):
          os.makedirs(filepath)

        filename = secure_filename(request.files[form.testFile.name].filename)

        if os.path.isfile(os.path.join(filepath, filename)):
          flash("This file already exists")
          return redirect(url_for('instructorProblemSettings', pid=p.id))

        request.files[form.testFile.name].save(os.path.join(filepath, filename))

        # Add the file to the problem
        p.testfiles.append(filename)
        p.save()


        #Create json spec file
        gradeSpec = {}

        gradeSpec['file'] = filename
        gradeSpec['type'] = form.testType.data
        gradeSpec['tests'] = testFileParsers[form.testType.data](os.path.join(filepath, filename))
        gradeSpec['sections'] = []

        filename += ".json"
        with open(os.path.join(filepath, filename), 'w') as f:
          json.dump(gradeSpec, f)

        flash("Added test file")
      else:
        flash("Form didn't validate", "error")

    return redirect(url_for('instructorProblemSettings', pid=p.id))
  except (Course.DoesNotExist, Problem.DoesNotExist, AssignmentGroup.DoesNotExist):
    abort(404)

@app.route('/editproblem/<pid>/remTestFile/<filename>')
@login_required
def remTestFile(pid, filename):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not c in current_user.courseInstructor:
      abort(403)

    filepath = getTestPath(c, a, p)
    filepath = os.path.join(filepath, filename)

    os.remove(filepath)
    os.remove(filepath+".json")

    p.testfiles.remove(filename)
    p.save()
    return redirect(url_for('instructorProblemSettings', pid=p.id))
  except (Course.DoesNotExist, Problem.DoesNotExist, AssignmentGroup.DoesNotExist):
    abort(404)


#
# Helper function for test information
#

def getTestInfo(fn):
  with open(fn+".json") as f:
    data = json.load(f)
  return (os.path.basename(fn), data["type"])
