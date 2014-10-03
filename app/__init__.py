# -*- coding: utf-8 -*-
import os

from flask import Flask
from flask.ext.login import LoginManager, current_user
from flask.ext.mongoengine import MongoEngine
from flask.ext.bootstrap import Bootstrap

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

@app.before_request
def beforeRequest():
  g.user = current_user

from models import *

from root import *
from accounts import *
from admin import *
from instructor import *
from problem import *

from students import *
