# -*- coding: utf-8 -*-

#import the app and the login manager
from app import app, loginManager

#Import the flask functions we need
from flask import g, request, render_template, redirect, url_for, flash
from flask.ext.login import current_user, login_required

#Import the models we need for these pages
from app.structures.models.course import *
from app.structures.models.stats import *

#import forms for this page
from app.structures.forms import ClockInForm, ClockOutForm

#python imports
from datetime import datetime

@app.route('/activegrutors')
def viewActiveGrutors():
  '''
  Function Type: View Function
  Template: activeGrutors.html
  Purpose: Display all the active grutors for the courses a user is taking

  Inputs: None

  Template Parameters:
    courses: A list of courses the user is in currently or is grading
    grutorLists: A dictionary mapping course IDs to lists of active graders
  '''

  ciForm = ClockInForm()
  ciForm.course.choices = [(str(c.id), c.name) for c in g.user.gradingActive()]

  courses = list(set(g.user.gradingActive() + g.user.studentActive()))
  grutorLists={}
  for c in courses:
    grutorLists[c.id] = TutoringSession.objects.filter(course=c.id, endTime=None)
  return render_template("common/activeGrutors.html", courses=courses, \
                          grutorLists=grutorLists,\
                          ciForm=ciForm, coForm=ClockOutForm(),\
                          grutoringCourses = TutoringSession.objects.filter(grutor=g.user.id, endTime=None))

@app.route('/activegrutors/clockin', methods=['POST'])
@login_required
def grutorClockIn():
  try:
    if request.method == 'POST':
      form = ClockInForm(request.form)
      form.course.choices = [(str(x.id), x.name) for x in g.user.gradingActive()]
      if form.validate():
        if form.location.data != "Other" or len(form.other.data) > 0:
          cid = form.course.data
          c = Course.objects.get(id=cid)

          #Check for security purposes
          if not c in g.user.gradingActive():
            abort(403)

          u = User.objects.get(id=current_user.id)

          s = TutoringSession.objects.filter(grutor=u, course=c, endTime=None)

          if len(s) == 0:
            s = TutoringSession()
            s.grutor = u
            s.course = c
            s.startTime = datetime.utcnow()
            s.endTime = None
            if form.location.data == "Other":
              s.location = form.other.data
            else:
              s.location = form.location.data
            s.save()
            flash("You have been signed in", "success")
          else:
            flash("You are already signed in", "warning")
        else:
          flash("You must provide a location if you select Other", "warning")
      else:
        flash("Form validation failed " + str(form.course.errors), "error")
    return redirect(url_for('viewActiveGrutors'))
  except Course.DoesNotExist:
    #If either p can't be found or we can't get its parents then 404
    abort(404)

@app.route('/activegrutors/clockout/<sid>', methods=['POST'])
@login_required
def grutorClockOut(sid):
  if request.method == 'POST':
    form = ClockOutForm(request.form)
    if form.validate():
      gs = TutoringSession.objects.get(id=sid)
      gs.endTime = datetime.utcnow()
      gs.comments = form.comments.data
      gs.save()
      flash("You have been signed out", "success")
  return redirect(url_for('viewActiveGrutors'))
