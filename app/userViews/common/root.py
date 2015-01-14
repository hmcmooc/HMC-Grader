# -*- coding: utf-8 -*-

#import the app and the login manager
from app import app, loginManager

#Import the flask functions we need
from flask import g, request, render_template, redirect, url_for, flash
from flask.ext.login import current_user, login_required

#Import the models we need for these pages
from app.structures.models.course import *
from app.structures.models.stats import *

#Import the forms needed on these pages

@app.route('/')
def index():
  '''
  Function Type: View Function
  Template: index.html/userindex.html
  Purpose: Display the index of the site to the users with a little welcome
  message. If the user is logged in display pertinant information for the user.

  Inputs: None

  Template Parameters:
  	active_page: A string indicating which page should be active in the nav-bar

    # If a user is authenticated
    attendForm: A form for allowing a student to mark attendance to class
    clockForm: A form for allowing a grutor to activate tutoring hours
    activeHours: A list of the classes a tutor is currently clocked into


  Forms Handled: None
  '''
  if g.user.is_authenticated():
    inProgress = Submission.objects.filter(gradedBy=g.user.id, status=3)

    return render_template("userindex.html", active_page="index", \
                            numInProgress=len(inProgress),\
                            inProgress=inProgress)
  return render_template("index.html", active_page="index")


#
# Error handling functions
#

@app.errorhandler(403)
def forbidden(e):
  '''
  Function Type: View Function
  Template: common/permission.html
  Purpose: Inform a user they don't have permission to access a page
  '''
  return render_template("common/permission.html")

@app.errorhandler(404)
def pageNotFound(e):
  '''
  Function Type: View Function
  Template: common/permission.html
  Purpose: Inform a user the page they wanted wasn't found
  '''
  return render_template("common/notfound.html")

@app.errorhandler(500)
def error(e):
  '''
  Function Type: View Function
  Template: common/permission.html
  Purpose: Inform a user that an error occured. Additionally display exception
  info and a traceback.
  '''
  import traceback
  tb = traceback.format_exc()
  flash(e, "error")
  flash(tb, "error")
  return render_template("common/error.html")
