# coding=utf-8

from flask import g, jsonify, flash
from flask.ext.login import login_required

from app.models.course import *

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
    removePath(getAssignmentPath(c, a))

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
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return jsonify(status=403), 403

    a = AssignmentGroup.objects.get(id=aid)
    p = Problem.objects.get(id=pid)

    flash("Problem "+a.name+"/"+p.name+" removed", "success")

    #Remove storage space
    removePath(getProblemPath(c, a, p))

    #We leverage mongo's reverse delete rules to remove the problem from the
    #assignment's problem list

    p.cleanup()
    #p.gradeColumn.delete()
    #a.problems.remove(p)
    p.delete()
    #a.save()

    return jsonify(status=200)
  except (Course.DoesNotExist, AssignmentGroup.DoesNotExist, Problem.DoesNotExist):
    return jsonify(status=404), 404
