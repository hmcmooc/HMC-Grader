from app import app

from flask import g, request, render_template, redirect, url_for, flash, send_file, abort
from flask import jsonify
from flask.ext.login import login_user, logout_user, current_user, login_required

from app.structures.models.user import *
from app.structures.models.gradebook import *
from app.structures.models.course import *

from app.helpers.filestorage import *

import os

@app.route('/student/<pid>/<uid>/<subnum>/reviewFiles')
@login_required
def studentViewFiles(pid, uid, subnum):
  try:
    problem = Problem.objects.get(id=pid)
    c, a = problem.getParents()
    if not (c in current_user.courseStudent or c in current_user.gradingCourses()):
      abort(403)

    u = User.objects.get(id=uid)
    return render_template('student/reviewfiles.html', problem=problem, subnum=subnum,\
                           user=u, course=c, assignment=a)
  except Problem.DoesNotExist:
    abort(404)

@app.route('/student/<pid>/<uid>/<subnum>/getFile', methods=['POST'])
@login_required
def studentGetFiles(pid, uid, subnum):
  try:
    problem = Problem.objects.get(id=pid)
    c, a = problem.getParents()
    if not (c in current_user.courseStudent or c in current_user.gradingCourses()):
      abort(403)

    u = User.objects.get(id=uid)
    s = problem.getSubmission(u, subnum)

    content = request.get_json()

    filepath = getSubmissionPath(c, a, problem, u, subnum)
    filepath = os.path.join(filepath, content['filename'])

    import magic

    fileType = magic.from_file(filepath, mime=True)
    fileType = fileType.split('/')

    if fileType[0] == 'text':
      with open(filepath, 'r') as f:
        return jsonify(majorType=fileType[0], minorType=fileType[1], content=f.read())
    else:
      return jsonify(majorType=fileType[0], minorType=fileType[1],\
       url=url_for('serveFiles', pid=pid, uid=uid, subnum=subnum, filename=content['filename']))
  except Problem.DoesNotExist:
    abort(404)

@app.route('/assignment/<pid>/<uid>/<subnum>/<filename>/serve')
@login_required
def serveFiles(pid, uid, subnum, filename):
  '''
  Function Type: Callback-Download
  Purpose: Downloads the file specified for the user.

  Inputs:
    pid: The object ID of the problem that the file belongs to
    uid: The object ID of the user the file belongs to
    subnum: The submission number that the file belongs to
    filename: The filename from the submission to download
  '''
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.courseStudent or c in current_user.gradingCourses()):
      abort(403)

    u = User.objects.get(id=uid)

    s = p.getSubmission(u, subnum)

    filepath = getSubmissionPath(c, a, p, u, subnum)

    return send_file(os.path.join(filepath, filename))
  except (Problem.DoesNotExist, Course.DoesNotExist, AssignmentGroup.DoesNotExist):
    #If either p can't be found or we can't get its parents then 404
    abort(404)


@app.route('/assignments/download/<pid>/<uid>/<subnum>/<filename>/download')
@login_required
def downloadFiles(pid, uid, subnum, filename):
  '''
  Function Type: Callback-Download
  Purpose: Downloads the file specified for the user.

  Inputs:
    pid: The object ID of the problem that the file belongs to
    uid: The object ID of the user the file belongs to
    subnum: The submission number that the file belongs to
    filename: The filename from the submission to download
  '''
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.courseStudent or c in current_user.gradingCourses()):
      abort(403)

    u = User.objects.get(id=uid)

    s = p.getSubmission(u, subnum)

    filepath = getSubmissionPath(c, a, p, u, subnum)

    return send_file(os.path.join(filepath, filename), as_attachment=True)
  except (Problem.DoesNotExist, Course.DoesNotExist, AssignmentGroup.DoesNotExist):
    #If either p can't be found or we can't get its parents then 404
    abort(404)
