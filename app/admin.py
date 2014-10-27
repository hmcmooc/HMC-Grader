
# -*- coding: utf-8 -*-

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for, flash
from flask.ext.login import login_user, logout_user, current_user, login_required

from flask.ext.mongoengine import DoesNotExist

from models import *
from forms import CreateCourseForm, CreateUserForm

'''
The administrator index view function
Renders the admin/index.html template.
This is the landing page for all administrator actions.
TODO: add content to this page to display load and stats of the server
'''
@app.route('/adminindex')
@login_required
def adminIndex():
  #even though we require login if someone gets here and is not admin
  #send them away. This is done in all methods for the admin panel
  if not g.user.isAdmin:
    return redirect(url_for('index'))

  #eventually we will compute statistics about the state of the system to be
  #put here
  return render_template('admin/index.html', active_page="index")

'''
The administrator course creation/edit view function
Renders the admin/courses.html template
This renders information about all of the courses in the system. From here you
can create new courses. Edit courses as the administrator and deactivate old
courses.

This function also handles the form submission for the creation of a new course

NOTE: We do not delete old courses so that the grades can stay in the system
and be viewed by students in the future.
'''
@app.route('/admincourses', methods=['POST', 'GET'])
@login_required
def adminCourses():
  #even though we require login if someone gets here and is not admin
  #send them away. This is done in all methods for the admin panel
  if not g.user.isAdmin:
    return redirect(url_for('index'))

  if request.method == "POST":
    form = CreateCourseForm(request.form)
    if form.validate():
      #create a new course
      c = Course()
      c.name = form.name.data
      c.semester = form.semester.data
      c.gradeBook = GradeBook()
      c.gradeBook.categories.append(GBCategory("Assignments"))
      c.save()
      return redirect(url_for('adminCourses'))
  return render_template('admin/courses.html', form=CreateCourseForm(), active_page="courses", courses=Course.objects)

'''
Intermediate view function for deactivating a course.
This view function gets called to deactivate a course and then redirects back
to the admin course administration page.

This function does not render any templates.
'''
@app.route('/admindeactivatecourse/<id>')
@login_required
def deactivateCourse(id):
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

'''
The administrator user creation and management of users
It renders the admin/users.html template
'''
@app.route('/adminusers')
@login_required
def adminUsers():
  return render_template('admin/users.html', form=CreateUserForm(), active_page="users", users=User.objects.order_by("+username"))

'''
A form handling view for the creation of a new user.
It accepts a post request with new user data attempts to create that user and
flashes errors back to the user if it fails.
It doesn't render any template instead it redirects to the adminUsers view.
'''
@app.route('/adminadduser', methods=['POST', 'GET'])
@login_required
def addUser():
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
