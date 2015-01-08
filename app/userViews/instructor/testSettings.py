# coding=utf-8

'''This module handles all functions responsible for modifying the course
settings page.

View Function: instructorEditTestFile (instructor/testSettings.html)

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

from app.structures.forms import ReuploadTestForm

#import plugins
from app.plugins.autograder import getTestFileParsers

#Generic python imports
import json
from werkzeug import secure_filename

@app.route('/editproblem/<pid>/editTestFile/<filename>')
@login_required
def instructorEditTestFile(pid, filename):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not c in current_user.courseInstructor:
      abort(403)

    filepath = getTestPath(c, a, p)
    filepath = os.path.join(filepath, filename)

    return render_template('instructor/testSettings.html', course=c, assignment=a,\
                            problem=p, filename=filename, \
                            data=getTestData(filepath), form=ReuploadTestForm())
  except (Course.DoesNotExist, Problem.DoesNotExist, AssignmentGroup.DoesNotExist):
    abort(404)

@app.route('/editproblem/<pid>/saveTestFile/<filename>', methods=['POST'])
@login_required
def instructorSaveTestFile(pid, filename):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      abort(403)

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
  except (Course.DoesNotExist, Problem.DoesNotExist, AssignmentGroup.DoesNotExist):
    abort(404)

@app.route('/editproblem/<pid>/reupTestFile/<filename>', methods=['POST'])
@login_required
def instructorReuploadTestFile(pid, filename):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not c in current_user.courseInstructor:
      abort(403)

    filepath = getTestPath(c, a, p)
    filepath = os.path.join(filepath, filename)

    gradeSpec = getTestData(filepath)
    parser = getTestFileParsers()[gradeSpec['type']]

    if request.method == "POST":
      form = ReuploadTestForm(request.form)
      if form.validate():
        filename = secure_filename(request.files[form.testFile.name].filename)

        if filename != gradeSpec['file']:
          flash("Uploaded file does not have the same name as the existing file. Reupload failed.", "warning")
          return redirect(url_for('instructorEditTestFile', pid=pid, filename=gradeSpec['file']))

        request.files[form.testFile.name].save(filepath)

        tests = parser(filepath)

        #Filter out removed tests
        for sec in gradeSpec['sections']:
          sec['tests'] = [x for x in sec['tests'] if x in tests]

        gradeSpec['tests'] = tests

        with open(filepath+".json", 'w') as f:
          json.dump(gradeSpec, f)
        flash("File successfully reuploaded", "success")

    return redirect(url_for('instructorEditTestFile', pid=pid, filename=filename))

  except (Course.DoesNotExist, Problem.DoesNotExist, AssignmentGroup.DoesNotExist):
    abort(404)

#
# Helper function for test data
#

def getTestData(fn):
  with open(fn+".json") as f:
    data = json.load(f)
  return data
