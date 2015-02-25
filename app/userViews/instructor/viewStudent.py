# coding=utf-8

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

#Import the forms needed on this page
#None

@app.route('/editcourse/<cid>/viewStudent/<uid>')
@login_required
def instructorViewStudent(cid, uid):
  '''
  Function Type: View Function
  Template: instructor/viewStudent.html
  Purpose: Allows an instructor to view a student

  Inputs:
    cid: The object ID of the course the student is in
    uid: The object ID of the student being viewed

  Template Parameters:
    course: The course object for this problem
    user: The student being viewed
  '''
  try:
    c = Course.objects.get(id=cid)
    u = User.objects.get(id=uid)

    if not c in current_user.courseInstructor:
      abort(403)

    return render_template("instructor/viewStudent.html", course=c, user=u)

  except (Course.DoesNotExist, User.DoesNotExist):
    abort(404)
