from app import db

class Page(db.Document):
  '''
  A document containing markdown formatted grading instructions
  '''

  title = db.StringField(default="Untitled Page")
  text = db.StringField(default="")

  course = db.ReferenceField('Course')

  #Can any person from the internet view this page
  perm = db.MapField(db.BooleanField())

  images = db.ListField(db.StringField())

  def initializePerms(self):
    self.perm['anyView'] = False
    self.perm['userView'] = False
    self.perm['cUserView'] = True
    self.perm['grutorView'] = False
    self.perm['cGrutorView'] = True

    self.perm['userEdit'] = False
    self.perm['cUserEdit'] = False
    self.perm['grutorEdit'] = False
    self.perm['cGrutorEdit'] = True

  def canView(self, user):
    return self.perm['anyView'] or \
      (user.is_authenticated() and self.perm['userView']) or\
      (user.is_authenticated() and self.perm['cUserView'] and \
        (self.course in user.courseStudent or \
         self.course in user.courseGrutor or \
         self.course in user.courseInstructor)) or\
      (user.is_authenticated() and self.perm['grutorView'] and \
        not self.course in user.courseStudent and  \
        len(user.gradingCourses()) > 0) or \
      (user.is_authenticated() and self.perm['cGrutorView'] and \
        self.course in user.gradingCourses()) or \
      (user.is_authenticated() and self.course in user.courseInstructor)

  def canEdit(self, user):
    return (user.is_authenticated() and self.perm['userEdit']) or\
      (user.is_authenticated() and self.perm['cUserEdit'] and \
        (self.course in user.courseStudent or \
         self.course in user.courseGrutor or \
         self.course in user.courseInstructor)) or\
      (user.is_authenticated() and self.perm['grutorEdit'] and \
        not self.course in user.courseStudent and  \
        len(user.gradingCourses()) > 0) or \
      (user.is_authenticated() and self.perm['cGrutorEdit'] and \
        self.course in user.gradingCourses()) or \
      (user.is_authenticated() and self.course in user.courseInstructor)
