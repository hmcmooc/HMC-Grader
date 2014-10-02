
# -*- coding: utf-8 -*-

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for, flash
from flask.ext.login import login_user, logout_user, current_user, login_required

from flask.ext.mongoengine import DoesNotExist

from models import *
from forms import CreateCourseForm, CreateUserForm

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
  return render_template('admin/users.html', form=CreateUserForm(), active_page="users", users=User.objects.order_by("+username"))

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
