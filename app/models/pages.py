from app import db

class Page(db.Document):
  '''
  A document containing markdown formatted grading instructions
  '''

  title = db.StringField(default="Untitled Page")
  text = db.StringField(default="")

  courses = db.ListField(db.ReferenceField('Course'))

  #Can any person from the internet view this page
  generalView = db.BooleanField(default=False)

  #Can students view
  studentView = db.BooleanField(default=True)

  #What can grutors do for this page
  grutorView = db.BooleanField(default=True)
  grutorEdit = db.BooleanField(default=True)
