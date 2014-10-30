# coding=utf-8

from app import app
import os

def getFilePath(course, assignment, problem, user, subnum):
  #Course path
  path = os.path.join(app.config['STORAGE_HOME'], course.semester, course.name)
  #Join assignment and problem
  path = os.path.join(path, assignment.name, problem.name)
  #Joun username and submission number
  path = os.path.join(path, user.username, str(subnum))

  #TODO: Clean the path by removing spaces and intermediate periods

  return path

def getTestPath(course, assignment, problem):
  #Course path
  path = os.path.join(app.config['STORAGE_HOME'], course.semester, course.name)
  #Join assignment and problem
  path = os.path.join(path, assignment.name, problem.name)

  #TODO: Clean the path by removing spaces and intermediate periods

  #Join test directory
  path = os.path.join(path, '.test')

  return path
