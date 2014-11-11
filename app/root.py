# -*- coding: utf-8 -*-

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for
from flask.ext.login import login_user, logout_user, current_user, login_required

from models.stats import *

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
  return render_template("index.html", active_page="index")
