# coding=utf-8

from app import db


class TutoringSession(db.Document):
  '''
  This data structure keeps track of the data for tutoring sessions.
  '''
  grutor = db.ReferenceField('User')

  startTime = db.DateTimeField()
  endTime = db.DateTimeField()

  course = db.ReferenceField('Course')
  location = db.StringField()

  comments = db.StringField()
