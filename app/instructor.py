# -*- coding: utf-8 -*-

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for, flash
from flask.ext.login import login_user, logout_user, current_user, login_required

from flask.ext.mongoengine import DoesNotExist

from models import *
from forms import CreateAssignmentForm, AddUserCourseForm, ProblemOptionsForm

import traceback, StringIO, sys
import dateutil.parser


'''
Base pages to display
'''

@app.route('/editcourse/<id>')
@login_required
def administerCourse(id):
  try:
    c = Course.objects.get(id=id)
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    #Get the users for this course
    s = User.objects.filter(courseStudent=c)
    grutor = User.objects.filter(courseGrutor=c)
    i = User.objects.filter(courseInstructor=c)

    return render_template("instructor/course.html",\
     course=c, students=s, grutors=grutor, instrs=i,\
     form=CreateAssignmentForm(), suserform=AddUserCourseForm(),\
     guserform=AddUserCourseForm(), iuserform=AddUserCourseForm())
  except Course.DoesNotExist:
    return redirect(url_for('adminIndex'))


'''
Modifying assignments
'''

@app.route('/assignment/<cid>/create', methods=['POST', 'GET'])
@login_required
def createAssignment(cid):
  if request.method == "POST":
    form = CreateAssignmentForm(request.form)
    if form.validate():
      try:
          c = Course.objects.get(id=cid)
          #For security purposes we send anyone who isnt an instructor or
          #admin away
          if not (g.user.isAdmin or c in current_user.courseInstructor):
            return redirect(url_for('index'))

          #If this assignment already exists we want to return now
          if form.name.data in c.assignments:
            flash("Assignment already exists")
            return redirect(url_for('administerCourse', id=cid))


          #Create the assignment and problem
          a = AssignmentGroup(form.name.data)
          a.save()
          c.assignments.append(a)

          #Create a GBEntry and GBColumn
          hw = c.gradeBook.getCategoryByName("Assignments")
          e = GBEntry(form.name.data)
          e.save()
          hw.entries.append(e)
          #Give the assignment its entry
          a.gradeEntry = e

          #Save the documents
          a.save()
          e.save()
          c.save()
          flash("Added Assignment Group")
          return redirect(url_for('administerCourse', id=cid))
      except Exception as e:
        raise e
  return redirect(url_for('administerCourse', id=cid))

@app.route('/assignment/<cid>/<aid>/addproblem')
@login_required
def addProblem(cid,aid):
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    a = AssignmentGroup.objects.get(id=aid)

    p = Problem("")
    p.save()

    gc = GBColumn("")
    gc.save()

    p.gradeColumn = gc
    p.save()

    a.problems.append(p)
    a.save()
    flash("This is your first time creating the problem please fill in all the form fields an hit save")
    return redirect(url_for('editProblem', cid=cid, aid=a.id, pid=p.id))
  except Exception as e:
    raise e


@app.route('/assignment/<cid>/<aid>/remproblem/<pid>')
@login_required
def remProblem(cid,aid,pid):
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    #a = AssignmentGroup.objects.get(id=aid)
    p = Problem.objects.get(id=pid)

    p.cleanup()
    #p.gradeColumn.delete()
    #a.problems.remove(p)
    p.delete()
    #a.save()

    return redirect(url_for('administerCourse', id=cid))
  except Course.DoesNotExist:
    pass

@app.route('/assignment/<cid>/<aid>/del')
@login_required
def delAssignment(cid, aid):
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    a = AssignmentGroup.objects.get(id=aid)
    c.assignments.remove(a)

    hw = c.gradeBook.getCategoryByName("Assignments")
    hw.entries.remove(a.gradeEntry)

    a.gradeEntry.delete()
    a.delete()
    c.save()
    flash("Assignment Group Removed")
  except Exception as e:
    raise e
  return redirect(url_for('administerCourse', id=cid))

'''
Adding and removing users from the course
'''

@app.route('/editcourse/<cid>/adduser', methods=['POST'])
@login_required
def addUserCourse(cid):
  try:
    c = Course.objects.get(id=cid)

    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))

    if request.method == "POST":
      form = AddUserCourseForm(request.form)
      if form.validate():
        u = User.objects.get(username=form.uname.data)
        if request.form['btn'] == "student":
          u.courseStudent.append(c)
        elif request.form['btn'] == "grutor":
          u.courseGrutor.append(c)
        else:
          u.courseInstructor.append(c)
        u.save()
  except User.DoesNotExist:
    flash("Failed to find user", "error")
  except Exception as e:
    raise e
  return redirect(url_for('administerCourse', id=cid))

@app.route('/editcourse/<cid>/remuser/<uid>/<t>')
@login_required
def remUserCourse(cid, uid, t):
  try:
    c = Course.objects.get(id=cid)

    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      return redirect(url_for('index'))


    u = User.objects.get(id=uid)
    if t == "student":
      u.courseStudent.remove(c)
    elif t == "grutor":
      u.courseGrutor.remove(c)
    else:
      u.courseInstructor.remove(c)
    u.save()

  except User.DoesNotExist:
    flash("Failed to find user")
  except Exception as e:
    raise e
  return redirect(url_for('administerCourse', id=cid))
