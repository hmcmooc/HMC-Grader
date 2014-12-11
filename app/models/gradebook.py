from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from mongoengine import NULLIFY, PULL

from app.helpers.filestorage import *

class GBGrade(db.Document):
  '''
  A grade contains a dictionary mapping rubric sections to scores.
  '''
  #Map score name (eg. GrutorScore or TestScore) to scores
  scores = db.MapField(db.DecimalField())

  def totalScore(self):
    return sum(self.scores.values())

class GBColumn(db.Document):
  '''
  A column represents a single list of entries. It can be a single problem or
  one days participation, or one test.
  '''
  name = db.StringField()
  maxScore = db.DecimalField(default=0)

  #Map usernames to grade entries
  scores = db.MapField(db.ReferenceField('GBGrade'))

  def __init__(self, name, **data):
    super(GBColumn, self).__init__(**data)
    self.name = name

  def cleanup(self):
    pass

class GBGroup(db.Document):
  '''
  Entries are designed to contain columns that are temporall related. Such as
  all of the problems in a certain week. (This level of granularity isn't
  accessible in the manual gradebook, this may be a source of a refactor)
  '''
  name = db.StringField(required=True)
  columns = db.ListField(db.ReferenceField('GBColumn', reverse_delete_rule=PULL))

  def __init__(self, name, **data):
    super(GBGroup, self).__init__(**data)
    self.name = name

  def cleanup(self):
    for c in self.columns:
      c.cleanup()
      c.delete()

  def getWidth(self):
    return max(len(self.columns), 1)


class GradeBook(db.EmbeddedDocument):
  '''
  The gradebook class is designed to contain all the information regarding
  grades for a course. Each Course has one Gradebook. A gradebook can group
  columns together with groups and groups are either for assignments or
  auxillary grades.
  '''

  assignmentGrades = db.ListField(db.ReferenceField('GBGroup'))
  auxillaryGrades = db.ListField(db.ReferenceField('GBGroup'))

  def getCategoryByName(self, name):
    for c in self.categories:
      if c.name == name:
        return c
    return None

  def cleanup(self):
    for c in self.categories:
      c.cleanup()

  def groups(self):
    for a in self.assignmentGrades:
      yield a
    for a in self.auxillaryGrades:
      yield a

  def columns(self):
    for a in self.assignmentGrades:
      if len(a.columns) == 0:
        yield None
      else:
        for c in sorted(a.columns, key=lambda x: x.name):
          yield c
    for a in self.auxillaryGrades:
      if len(a.columns) == 0:
        yield None
      else:
        for c in a.columns:
          yield c
