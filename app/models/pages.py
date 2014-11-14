from app import db

class Page(db.Document):
  '''
  A document containing markdown formatted grading instructions
  '''

  text = db.StringField(default="")
