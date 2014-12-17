# coding=utf-8

from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from mongoengine import NULLIFY, PULL


class GraderStats(db.Document):
  '''
  This datastructure is designed to determine when graders are at which
  tutoring hours
  '''
  user = db.ReferenceField('User')
  course = db.ReferenceField('Course')
  clockIn = db.DateTimeField()
  clockOut = db.DateTimeField()
  location = db.StringField()


class StudentStats(db.Document):
  '''
  This datastructure is designed to determine when students are using tutoring
  hours so we may better provide tutoring.
  '''
  user = db.ReferenceField('User')
  course = db.ReferenceField('Course')
  clockIn = db.DateTimeField()
