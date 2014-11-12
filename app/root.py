# -*- coding: utf-8 -*-

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for, flash
from flask.ext.login import login_user, logout_user, current_user, login_required

from models.stats import *
from app.forms import AttendanceForm, ClockInForm

@app.route('/')
def index():
  '''
  Function Type: View Function
  Template: index.html
  Purpose: Display the index of the site to the useers with a little welcome
  message.

  Inputs: None

  Template Parameters:
  	active_page: A string indicating which page should be active in the nav-bar

  Forms Handled: None
  '''
  if g.user.is_authenticated():
    attendForm = AttendanceForm()
    attendForm.course.choices = [(str(x.id), x.name) for x in g.user.studentActive()]

    clockForm = ClockInForm()
    clockForm.course.choices = [(str(x.id), x.name) for x in g.user.gradingActive()]

    activeHours = GraderStats.objects.filter(user=g.user.id, clockOut=None)
    return render_template("userindex.html", active_page="index", \
                            attendForm=attendForm, clockForm=clockForm,\
                            activeHours=activeHours)
  return render_template("index.html", active_page="index")

@app.route('/error')
def error():
  return render_template("error.html")

@app.route('/activegrutors')
def viewActiveGrutors():
  courses = list(set(g.user.studentActive()+g.user.gradingActive()))
  grutorLists = {}
  for c in courses:
    grutorLists[c.id] = GraderStats.objects.filter(course=c, clockOut=None) 
  return render_template("activeGrutors.html", courses=courses, \
                          grutorLists=grutorLists)
