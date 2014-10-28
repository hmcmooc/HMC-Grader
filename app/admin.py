
# -*- coding: utf-8 -*-

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for, flash
from flask.ext.login import login_user, logout_user, current_user, login_required

from flask.ext.mongoengine import DoesNotExist

from models import *
from forms import CreateCourseForm, CreateUserForm

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
    return redirect(url_for('index'))

  #eventually we will compute statistics about the state of the system to be
  #put here
  return render_template('admin/index.html', active_page="index")


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
      c = Course()
      c.name = form.name.data
      c.semester = form.semester.data
      c.gradeBook = GradeBook()
      c.gradeBook.categories.append(GBCategory("Assignments"))
      c.save()
      return redirect(url_for('adminCourses'))
  return render_template('admin/courses.html', form=CreateCourseForm(), active_page="courses", courses=Course.objects)


@app.route('/admindeactivatecourse/<id>')
@login_required
def deactivateCourse(id):
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
    course = Course.objects.get(id=id)
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
