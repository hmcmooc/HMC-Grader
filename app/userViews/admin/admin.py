# -*- coding: utf-8 -*-

'''
This module handles all administrator views and functions.
'''

#import the app and the celery object (for stats)
from app import app, celery

from flask import g, request, render_template, redirect, url_for, flash, jsonify
from flask import abort
from flask.ext.login import login_user, logout_user, current_user, login_required

from app.structures.models.user import *
from app.structures.models.gradebook import *
from app.structures.models.course import *
from app.structures.models.pages import *

from app.structures.forms import CreateCourseForm, CreateUserForm

from app.helpers.filestorage import ensurePathExists, getCoursePath

import psutil

#TODO: Add the statistics rendering
@app.route('/adminindex')
@login_required
def adminIndex():
  '''
  Function Type: View Function
  Template: admin/index.html
  Purpose: Landing page for an administrator. Additionally will display
  statistics about the status of the server.

  Inputs: None

  Template Parameters:
    actvie_page: A string for highlighting the active page in the nav-bar.

  Forms Handled: None
  '''
  #even though we require login if someone gets here and is not admin
  #send them away. This is done in all methods for the admin panel
  if not g.user.isAdmin:
    abort(403)

  import urllib2,json

  if not app.config['FLOWER_ACCESS_URL'] == None:
    resp = urllib2.urlopen(app.config['FLOWER_ACCESS_URL'] + '/api/workers')
    workers = json.loads(resp.read())
  else:
    workers = {}

  #eventually we will compute statistics about the state of the system to be
  #put here
  return render_template('admin/index.html', active_page="index", workers=workers)


@app.route('/admincourses', methods=['POST', 'GET'])
@login_required
def adminCourses():
  '''
  Function Type: View Function
  Template: admin/courses.html
  Purpose: Display all courses in the system and facilitate the creation of new
  courses.

  Inputs: None

  Template Parameters:
    active_page: A string for highlighting the active page in the nav-bar.
    form: A CreateCourseForm that is used to allow a user to input new course
    information.

  Forms Handled:
    CreateCourseForm: Validates the form and creates a new course with the
    specified name and semester.
  '''
  #even though we require login if someone gets here and is not admin
  #send them away. This is done in all methods for the admin panel
  if not g.user.isAdmin:
    return redirect(url_for('index'))

  if request.method == "POST":
    form = CreateCourseForm(request.form)
    if form.validate():
      #create a new course
      #TODO: Validate that a course with this name and semester doesn't already
      #exist
      try:
        c = Course.objects.get(name=form.name.data, semester=form.semester.data)
        flash("A course with this name and semester already exists", "warning")
      except Course.DoesNotExist:
        c = Course()
        c.name = form.name.data
        c.semester = form.semester.data
        c.gradeBook = GradeBook()
        c.save()

        page = Page()
        page.initializePerms()
        page.perm['anyView'] = True
        page.title = "Home"
        page.course = c
        page.save()

        c.homepage = url_for('viewPage', pgid=page.id)
        c.save()

        #Create the file backing
        ensurePathExists(getCoursePath(c))
        for admin in User.objects.filter(isAdmin=True):
          admin.courseInstructor.append(c)
          admin.save()
      return redirect(url_for('adminCourses'))
  return render_template('admin/courses.html', form=CreateCourseForm(), active_page="courses", courses=Course.objects)


@app.route('/admindeactivatecourse/<cid>')
@login_required
def deactivateCourse(cid):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Deactivate the course specified by <cid> and return to the admin
  course administration page.

  Inputs:
    cid: An object ID belonging to the course to deactivate

  Forms Handled: None
  '''
  #even though we require login if someone gets here and is not admin
  #send them away. This is done in all methods for the admin panel
  if not g.user.isAdmin:
    return redirect(url_for('index'))

  try:
    course = Course.objects.get(id=cid)
    course.isActive = False
    course.save()
    return redirect(url_for('adminCourses'))
  except Course.DoesNotExist:
    return redirect(url_for('adminCourses'))


@app.route('/adminusers')
@login_required
def adminUsers():
  '''
  Function Type: View Function
  Template: admin/users.html
  Purpose: Display all users in the system and facilitate creation of new users

  Inputs: None

  Template Parameters:
    form: A CreateUserForm that allows new user information to be entered
    active_page: A string for highlighting the active page in the nav-bar

  Forms Handled: None
  '''
  return render_template('admin/users.html', form=CreateUserForm(), active_page="users", users=User.objects.order_by("+username"))


@app.route('/adminadduser', methods=['POST', 'GET'])
@login_required
def addUser():
  '''
  Function Type: Callback-Redirect Function
  Purpose: Handle a CreateUserForm and create a new user in the course

  Inputs: None

  Forms Handled:
    CreateUserForm: Checks if the username exists. If it doesn't exist
    it will create a new user with the specified information.
  '''
  if request.method == "POST":
    form = CreateUserForm(request.form)
    if form.validate():
      try:
        u = User.objects.get(username=form.username.data)
        flash("Username already exists")
        return redirect(url_for('adminUsers'))
      except User.DoesNotExist:
        u = User()
        u.firstName = form.firstName.data
        u.lastName = form.lastName.data
        u.email = form.email.data
        u.username = form.username.data
        if form.password.data == "":
          u.setPassword("asdf")
        else:
          u.setPassword(form.password.data)
        u.save()
  return redirect(url_for('adminUsers'))

@app.route('/admin/switch/<uid>')
@login_required
def adminSwitch(uid):
  if not g.user.isAdmin:
    return redirect(url_for('index'))

  user = User.objects.get(id=uid)
  logout_user()
  login_user(user)
  g.user = current_user
  return redirect(url_for('index'))

@app.route('/admin/rem/<uid>')
@login_required
def adminRemove(uid):
  if not g.user.isAdmin:
    return redirect(url_for('index'))

  user = User.objects.get(id=uid)
  user.delete()
  return redirect(url_for('adminUsers'))

#
# Admin AJAX functions
#

@app.route('/admin/data/celery', methods=['GET'])
@login_required
def adminDataCelery():
  try:
    i = celery.control.inspect()
    queueDict = i.reserved()
    queue = []
    for k in queueDict:
      queue.append([k, queueDict[k]])
    return jsonify(queue=queue)
  except Exception as e:
    return jsonify(queue=str(e))
