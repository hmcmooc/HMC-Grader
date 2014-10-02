# -*- coding: utf-8 -*-

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for
from flask.ext.login import login_user, logout_user, current_user, login_required

@app.route('/')
def index():
  return render_template("index.html", active_page="index")
