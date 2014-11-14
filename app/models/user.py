# coding=utf-8

from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from mongoengine import NULLIFY, PULL

from app.filestorage import *

'''
User model(s)
'''
class User(db.Document):
  '''
  The information for one user of the system (Student, Grader, or Instructor)
  '''
  #General user information
  firstName = db.StringField()
  lastName = db.StringField()
  username = db.StringField(required=True, unique=True)
  email = db.EmailField()
  passHash = db.StringField(max_length=512)
  photoName = db.StringField()

  #What courses are they teaching/in
  courseStudent    = db.ListField(db.ReferenceField('Course'))
  courseGrutor     = db.ListField(db.ReferenceField('Course'))
  courseInstructor = db.ListField(db.ReferenceField('Course'))

  #Is this user an admin
  isAdmin = db.BooleanField(default=False)

  def is_authenticated(self):
    return True

  def is_active(self):
    return True

  def is_anonymous(self):
    return False

  def get_id(self):
    return unicode(self.id)

  def setPassword(self, pw):
    self.passHash = generate_password_hash(pw)

  def checkPassword(self, pw):
    return check_password_hash(self.passHash, pw)

  def gradingCourses(self):
    out = self.courseGrutor + self.courseInstructor
    out = list(set(out))
    return out

  def gradingActive(self):
    out = self.grutorActive() + self.instructorActive()
    out = list(set(out))
    return out

  def studentActive(self):
    return [x for x in self.courseStudent if x.isActive]

  def grutorActive(self):
    return [x for x in self.courseGrutor if x.isActive]

  def instructorActive(self):
    return [x for x in self.courseInstructor if x.isActive]
