from app import app

from flask import g, request, render_template, redirect, url_for, flash, send_file, abort
from flask import jsonify
from flask.ext.login import login_user, logout_user, current_user, login_required

from app.structures.models.user import *
from app.structures.models.gradebook import *
from app.structures.models.course import *

from app.helpers.filestorage import *

import codecs

import os

@app.route('/grutor/<pid>/getFile', methods=['POST'])
@login_required
def grutorGetFiles(pid):
  try:
    problem = Problem.objects.get(id=pid)
    c, a = problem.getParents()
    if not (c in current_user.gradingCourses()):
      abort(403)

    content = request.get_json()

    filepath = getTestPath(c, a, problem)
    filepath = os.path.join(filepath, content['filename'])

    import magic

    fileType = magic.from_file(filepath, mime=True)
    fileType = fileType.split('/')

    if fileType[0] == 'text':
      try:
        f = codecs.open(filepath, encoding='utf-8', errors='ignore')
        content = f.read()
        return jsonify(majorType=fileType[0], minorType=fileType[1], content=content)
      except Exception as e:
        return jsonify(majorType=fileType[0], minorType=fileType[1], content=str(e))
        pass
      finally:
        f.close()
    else:
      return jsonify(majorType=fileType[0], minorType=fileType[1],\
       url=url_for('grutorServeFiles', pid=pid, filename=content['filename']))
  except Problem.DoesNotExist:
    abort(404)

@app.route('/grutor/<pid>/test/<filename>/serve')
@login_required
def grutorServeFiles(pid, filename):
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
    if not (c in current_user.gradingCourses()):
      abort(403)

    filepath = getTestPath(c, a, p)

    return send_file(os.path.join(filepath, filename))
  except (Problem.DoesNotExist, Course.DoesNotExist, AssignmentGroup.DoesNotExist):
    #If either p can't be found or we can't get its parents then 404
    abort(404)


@app.route('/grutor/<pid>/test/download/<path:filename>')
@login_required
def grutorDownloadFiles(pid, filename):
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
    if not (c in current_user.gradingCourses()):
      abort(403)


    filepath = getTestPath(c, a, p)

    return send_file(os.path.join(filepath, filename), as_attachment=True)
  except (Problem.DoesNotExist, Course.DoesNotExist, AssignmentGroup.DoesNotExist):
    #If either p can't be found or we can't get its parents then 404
    abort(404)
