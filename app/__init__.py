# -*- coding: utf-8 -*-
import os, sys

from flask import Flask, g
from flask.ext.login import LoginManager, current_user
from flask.ext.mongoengine import MongoEngine
from flask.ext.bootstrap import Bootstrap
from flask.ext.markdown import Markdown

#import for celery task manager
from helpers.celeryconfig import make_celery

from markdown.extensions.attr_list import AttrListExtension


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
markdown = Markdown(app)
markdown.register_extension(AttrListExtension)

#Initialize the celery object
celery = make_celery(app)

#Before each request we should store our current user (provided by flask-login)
#in the global object g (which is accessable inside templates)
@app.before_request
def beforeRequest():
  g.user = current_user

#Add the custom converters we have made here
from app.helpers.converters import BoolConverter, TimeConverter

app.url_map.converters['bool'] = BoolConverter
app.url_map.converters['time'] = TimeConverter

#We pre imort all the models because they have a required import order.
#By doing this here we remove that requirement in other files which makes
#extending the code easier.
from structures.models.gradebook import *
from structures.models.course import *
from structures.models.user import *
from structures.models.stats import *
from structures.models.pages import *


#Set up a function that can be used in jinja
def activeCourses():
  return Course.objects.filter(isActive=True)

#Makes list of tuples
#(Depth, isDirectory, name, path)
def walkFileTree(filepath):
  from os import listdir
  from os.path import isfile, isdir, join
  def increaseDepth(prevFile):
    def f(tup):
      return (tup[0]+1, tup[1], tup[2], join(prevFile,tup[3]))
    return f

  out = []
  for f in os.listdir(filepath):
    if isfile(join(filepath, f)):
      out.append((0, False, f, f))
    else:
      out.append((0, True, f, f))
      out += map(increaseDepth(f), walkFileTree(join(filepath, f)))

  return out




app.jinja_env.globals.update(activeCourses=activeCourses)
app.jinja_env.globals.update(walkFileTree=walkFileTree)

#We import all of the various modules in userViews. These modules contain functions
#which generate URL->enpoint bindings which allows the pages to be rendered or
#allows redirects and AJAX calls to be executed
from userViews.common import *
from userViews.admin import *
from userViews.instructor import *
from userViews.student import *
from userViews.grutor import *
