# -*- coding: utf-8 -*-
import os, sys

from flask import Flask
from flask.ext.login import LoginManager, current_user
from flask.ext.mongoengine import MongoEngine
from flask.ext.bootstrap import Bootstrap
from flask.ext.markdown import Markdown

#import for celery task manager
from celeryconfig import make_celery

from decimal import getcontext

#Set decimal precision
getcontext.prec = 2

app = Flask(__name__)

#Load the configuration file config.py
app.config.from_object('config')

#Load default bootstrap templates
Bootstrap(app)

#Initialize the login system
loginManager = LoginManager()
loginManager.init_app(app)
loginManager.login_view = 'login' #Set the default view for logging in

#Initialize the database connection
db = MongoEngine(app)

#Initialize the markdown engine
Markdown(app)

#Initialize the celery object
celery = make_celery(app)

#Before each request we should store our current user (provided by flask-login)
#in the global object g (which is accessable inside templates)
@app.before_request
def beforeRequest():
  g.user = current_user


from models.gradebook import *
from models.course import *
from models.user import *

#We perform imports here for all the other files which contain pages
#By importing these here the decorators execute and the view functions become
#available. If you add another file with view functions you must import it here
from root import *
from accounts import *
from admin import *
from instructor import *
from students import *
from grutor import *
