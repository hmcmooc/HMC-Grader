# -*- coding: utf-8 -*-

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for, flash
from flask.ext.login import login_user, logout_user, current_user, login_required

from flask.ext.mongoengine import DoesNotExist

from models import *
from forms import ProblemOptionsForm, AddTestForm

from werkzeug import secure_filename

import traceback, StringIO, sys
import dateutil.parser
from decimal import *
import json, os

from autograder.pythongrader import pythonTestParser

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

    testFiles = []
    for f in p.testfiles:
      testFiles.append(getTestInfo(f))

    return render_template("instructor/problem.html", course=c, problem=p, assignment=a,\
                           form=ProblemOptionsForm(), testForm=AddTestForm(),\
                           testFiles=testFiles)
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

@app.route('/editcourse/<cid>/<aid>/p/<pid>/addrubricsection', methods=['GET'])
@login_required
def addRubricSec(cid, aid, pid):
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    p = Problem.objects.get(id=pid)

    p.rubric[request.args['name']] = Decimal(request.args['points'])

    #update the column score in the gradebook
    p.gradeColumn.maxScore = p.totalPoints()
    p.gradeColumn.save()

    p.save()
  except Exception as e:
    flash(str(e))
  return redirect(url_for('editProblem', cid=cid, aid=aid, pid=pid))

@app.route('/editcourse/<cid>/<aid>/p/<pid>/delrubricsection/<name>', methods=['GET'])
@login_required
def delRubricSec(cid, aid, pid, name):
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    p = Problem.objects.get(id=pid)

    del p.rubric[name]

    #update the column score in the gradebook
    p.gradeColumn.maxScore = p.totalPoints()
    p.gradeColumn.save()

    p.save()
  except Exception as e:
    flash(str(e))
  return redirect(url_for('editProblem', cid=cid, aid=aid, pid=pid))

@app.route('/editcourse/problem/<pid>/addTestFile', methods=['POST'])
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
      if form.validate():
        filepath = os.path.join(app.config['GROODY_HOME'],c.semester,c.name,a.name,p.name,'.tests')

        if not os.path.isdir(filepath):
          os.makedirs(filepath)

        filename = secure_filename(request.files[form.testFile.name].filename)

        if os.path.isdir(os.path.join(filepath, filename)):
          flash("This file already exists")
          return redirect(url_for('editProblem', cid=c.id, pid=p.id, aid=a.id))

        request.files[form.testFile.name].save(os.path.join(filepath, filename))

        # Add the file to the problem
        p.testfiles.append(os.path.join(filepath, filename))
        p.save()

        #Create json spec file
        gradeSpec = {}

        gradeSpec['file'] = filename
        gradeSpec['type'] = form.testType.data
        gradeSpec['tests'] = pythonTestParser(os.path.join(filepath, filename))
        gradeSpec['sections'] = []

        filename += ".json"
        with open(os.path.join(filepath, filename), 'w') as f:
          json.dump(gradeSpec, f)

        flash("Added test file")
      else:
        flash("Form didn't validate", "error")

    return redirect(url_for('editProblem', cid=c.id, pid=p.id, aid=a.id))
  except Exception as e:
    flash(str(e), "error")
    return redirect(url_for('index'))

@app.route('/editcourse/problem/<pid>/editTestFile/<filename>')
@login_required
def editTestFile(pid, filename):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    return render_template('instructor/testedit.html', course=c, assignment=a,\
                            problem=p, filename=filename)
  except Exception as e:
    flash(str(e), "error")
    return redirect(url_for('editProblem', cid=c.id, pid=p.id, aid=a.id))

@app.route('/editcourse/problem/<pid>/remTestFile/<filename>')
@login_required
def remTestFile(pid, filename):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    filepath = os.path.join(app.config['GROODY_HOME'],c.semester,c.name,a.name,p.name,'.tests')
    filepath = os.path.join(filepath, filename)

    os.remove(filepath)
    os.remove(filepath+".json")

    p.testfiles.remove(filepath)
    p.save()
    return redirect(url_for('editProblem', cid=c.id, pid=p.id, aid=a.id))
  except Exception as e:
    flash(str(e), "error")
    return redirect(url_for('editProblem', cid=c.id, pid=p.id, aid=a.id))


def getTestInfo(fn):
  with open(fn+".json") as f:
    data = json.load(f)
  return (os.path.basename(fn), data["type"])
