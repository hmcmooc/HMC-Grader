# coding=utf-8
'''
This module handles all functions responsible for displaying the course
statistics.

View Function: instructorCourseStats

Redirect Functions: None

AJAX Functions: TODO
'''

#Import the app
from app import app

#Import needed flask functions
from flask import g, render_template, redirect, url_for, flash, jsonify, abort
from flask.ext.login import current_user, login_required

#Import the models we need on these pages
from app.structures.models.user import *
from app.structures.models.gradebook import *
from app.structures.models.course import *
