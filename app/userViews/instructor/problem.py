# -*- coding: utf-8 -*-

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for, flash, jsonify
from flask.ext.login import login_user, logout_user, current_user, login_required

from flask.ext.mongoengine import DoesNotExist

from app.models.user import *
from app.models.gradebook import *
from app.models.course import *

from app.forms import ProblemOptionsForm, AddTestForm

from werkzeug import secure_filename

from app.helpers.filestorage import *

import traceback, StringIO, sys
import dateutil.parser
from decimal import *
import json, os

from app.autograder import getTestFileParsers
from app.helpers.filestorage import moveProblemPath, getProblemPath

@app.route('/editproblem/<pid>')
@login_required
def editProblem(pid):
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

@app.route('/editproblem/<pid>/update', methods=['POST'])
@login_required
def updateProblem(pid):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))


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

        p.save()
  except Exception as e:
    flash(str(e))
  return redirect(url_for('editProblem', pid=pid))

@app.route('/editproblem/<pid>/addrubricsection', methods=['GET'])
@login_required
def addRubricSec(pid):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    p.rubric[request.args['name']] = Decimal(request.args['points'])

    #update the column score in the gradebook
    p.gradeColumn.maxScore = p.totalPoints()
    p.gradeColumn.save()

    p.save()
  except Exception as e:
    flash(str(e))
  return redirect(url_for('editProblem', pid=pid))

@app.route('/editproblem/<pid>/delrubricsection/<name>', methods=['GET'])
@login_required
def delRubricSec(pid, name):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    del p.rubric[name]

    #update the column score in the gradebook
    p.gradeColumn.maxScore = p.totalPoints()
    p.gradeColumn.save()

    p.save()
  except Exception as e:
    flash(str(e))
  return redirect(url_for('editProblem', pid=pid))

@app.route('/editproblem/<pid>/addTestFile', methods=['POST'])
@login_required
def addTestFile(pid):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    if request.method == "POST":
      form = AddTestForm(request.form)

      testFileParsers = getTestFileParsers()
      form.testType.choices = [(x,x) for x in testFileParsers.keys()]
      if form.validate():
        filepath = getTestPath(c, a, p)

        if not os.path.isdir(filepath):
          os.makedirs(filepath)

        filename = secure_filename(request.files[form.testFile.name].filename)

        if os.path.isdir(os.path.join(filepath, filename)):
          flash("This file already exists")
          return redirect(url_for('editProblem', pid=p.id))

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

    return redirect(url_for('editProblem', pid=p.id))
  except Exception as e:
    flash(str(e), "error")
    return redirect(url_for('index'))

@app.route('/editproblem/<pid>/editTestFile/<filename>')
@login_required
def editTestFile(pid, filename):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    filepath = getTestPath(c, a, p)
    filepath = os.path.join(filepath, filename)

    return render_template('instructor/testedit.html', course=c, assignment=a,\
                            problem=p, filename=filename, \
                            data=getTestData(filepath))
  except Exception as e:
    flash(str(e), "error")
    return redirect(url_for('editProblem', pid=p.id))

@app.route('/editproblem/<pid>/remTestFile/<filename>')
@login_required
def remTestFile(pid, filename):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    filepath = getTestPath(c, a, p)
    filepath = os.path.join(filepath, filename)

    os.remove(filepath)
    os.remove(filepath+".json")

    p.testfiles.remove(filename)
    p.save()
    return redirect(url_for('editProblem', pid=p.id))
  except Exception as e:
    flash(str(e), "error")
    return redirect(url_for('editProblem', pid=p.id))

@app.route('/editproblem/<pid>/saveTestFile/<filename>', methods=['POST'])
@login_required
def saveTestFile(pid, filename):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return jsonify(res=False)

    #Try to get the contents
    content = request.get_json()

    #make sure we got the contents
    if content == None:
      return jsonify(res=False)

    filepath = getTestPath(c, a, p)
    filepath = os.path.join(filepath, filename+".json")

    with open(filepath, 'w') as f:
      json.dump(content, f)

    return jsonify(res=True)
  except Exception as e:
    return jsonify(res="Exception raised: "+ str(e))

def getTestData(fn):
  with open(fn+".json") as f:
    data = json.load(f)
  return data

def getTestInfo(fn):
  with open(fn+".json") as f:
    data = json.load(f)
  return (os.path.basename(fn), data["type"])
