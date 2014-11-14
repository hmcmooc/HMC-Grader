from app import db

class Page(db.Document):
  '''
  A document containing markdown formatted grading instructions
  '''

  data = db.StringField()
