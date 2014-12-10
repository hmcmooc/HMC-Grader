# coding=utf-8

'''
This module handles all of the ajax requests for the course properties page of
the instructor tab.
'''

from flask import g, jsonify, flash, request
from flask.ext.login import login_required

from app.models.course import *
import string, random, shutil

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
    if not (g.user.isAdmin or c in g.user.courseInstructor):
      return jsonify(res=False, msg="Permission Denied")

    content = request.get_json()
    c.anonymousGrading = content['anonymousGrading']
    c.lateGradePolicy = content['lateGradePolicy']
    c.save()
    return jsonify(res=True)
  except Exception as e:
    return jsonify(res=False, msg=str(e))

@app.route('/assignment/<cid>/<aid>/del')
@login_required
def delAssignment(cid, aid):
  '''
  Function Type: Callback-AJAX Function
  Purpose: Delete an assignment and all problems in that assignment.

  Inputs:
    cid: The object ID of the course the assignment is in
    aid: The object ID of the assignment group to add the problem to

  Forms Handled: None
  '''
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in g.user.courseInstructor):
      return jsonify(status=403), 403


    a = AssignmentGroup.objects.get(id=aid)

    flash("Assignment group "+a.name+" removed", "success")

    #Remove the filestorage
    randString = ''.join(random.choice(string.letters + string.digits) for _ in range(10))
    assignPath = getAssignmentPath(c, a)
    shutil.move(assignPath, assignPath+'_'+randString)

    c.assignments.remove(a)

    c.gradeBook.assignmentGrades.remove(a.gradeEntry)

    a.gradeEntry.cleanup()
    a.gradeEntry.delete()
    a.cleanup()
    a.delete()
    c.save()
  except Course.DoesNotExist:
    return jsonify(status=404), 404
  except AssignmentGroup.DoesNotExist:
    pass
  return jsonify(status=200)


@app.route('/assignment/<cid>/<aid>/remproblem/<pid>')
@login_required
def remProblem(cid,aid,pid):
  '''
  Function Type: Callback-AJAX Function
  Purpose: Remove a problem from a specified assignment.

  Inputs:
    cid: The object ID of the course the assignment is in
    aid: The object ID of the assignment group to add the problem to
    pid: The object ID of the problem to remove

  Forms Handled: None
  '''
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in g.user.courseInstructor):
      return jsonify(status=403), 403

    a = AssignmentGroup.objects.get(id=aid)
    p = Problem.objects.get(id=pid)

    flash("Problem "+a.name+"/"+p.name+" removed", "success")

    #Remove storage space
    randString = ''.join(random.choice(string.letters + string.digits) for _ in range(10))
    probPath = getProblemPath(c, a, p)
    shutil.move(probPath, probPath+'_'+randString)
    #removePath(getProblemPath(c, a, p))

    #We leverage mongo's reverse delete rules to remove the problem from the
    #assignment's problem list

    p.cleanup()
    p.delete()

    return jsonify(status=200)
  except (Course.DoesNotExist, AssignmentGroup.DoesNotExist, Problem.DoesNotExist):
    return jsonify(status=404), 404
