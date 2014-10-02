from app import db
from werkzeug.security import generate_password_hash, check_password_hash

'''
User model(s)
'''
class User(db.Document):
  #General user information
  firstName = db.StringField()
  lastName = db.StringField()
  username = db.StringField(required=True)
  email = db.EmailField()
  passHash = db.StringField(max_length=512)

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


'''
Grade book models
'''
class GradeBook(db.EmbeddedDocument):
  categories = db.ListField(db.EmbeddedDocumentField('GBCategory'))

  def getCategoryByName(self, name):
    for c in self.categories:
      if c.name == name:
        return c
    return None

class GBCategory(db.EmbeddedDocument):
  name = db.StringField(required=True)
  entries = db.ListField(db.ReferenceField('GBEntry'))

  def __init__(self, name, **data):
    super(GBCategory, self).__init__(**data)
    self.name = name

class GBEntry(db.Document):
  name = db.StringField(required=True)
  columns = db.ListField(db.ReferenceField('GBColumn'))

  def __init__(self, name, **data):
    super(GBEntry, self).__init__(**data)
    self.name = name

class GBColumn(db.Document):
  name = db.StringField()
  maxScore = db.DecimalField(default=0)

  #Map usernames to grade entries
  scores = db.MapField(db.ReferenceField('GBGrade'))


  def __init__(self, name, **data):
    super(GBColumn, self).__init__(**data)
    self.name = name

class GBGrade(db.Document):
  #Map score name (eg. GrutorScore or TestScore) to scores
  scores = db.MapField(db.DecimalField())


'''
Course and submission models
'''

class Course(db.Document):
  #Identification information
  name = db.StringField(required=True)
  semester = db.StringField(required=True)

  #Information for grading and submission
  gradeBook = db.EmbeddedDocumentField('GradeBook')
  assignments = db.ListField(db.ReferenceField('AssignmentGroup'))

  #Is this course still being taught at this time
  isActive = db.BooleanField(default=True)


class AssignmentGroup(db.Document):
  name = db.StringField(required=True)
  gradeEntry = db.ReferenceField('GBEntry')
  problems = db.ListField(db.ReferenceField('Problem'))

  def __init__(self, name, **data):
    super(AssignmentGroup, self).__init__(**data)
    self.name = name

class Problem(db.Document):
  name = db.StringField()
  gradeColumn = db.ReferenceField('GBColumn')
  duedate = db.DateTimeField()
  rubric = db.MapField(db.DecimalField())

  #Map usernames to submission lists
  studentSubmissions = db.MapField(db.EmbeddedDocumentField('StudentSubmissionList'))

  def __init__(self, name, **data):
    super(Problem, self).__init__(**data)
    self.name = name

  def totalPoints(self):
    total = 0
    for k in self.rubric:
      total += self.rubric[k]
    return total

class StudentSubmissionList(db.EmbeddedDocument):
  submissions = db.ListField(db.EmbeddedDocumentField('Submission'))
  partners = db.ListField(db.ReferenceField('User'))

class Submission(db.EmbeddedDocument):
  submissionTime = db.DateTimeField(required=True)
  isLate = db.BooleanField(default=False)
  filePath = db.StringField(required=True)
  grade = db.ReferenceField('GBGrade')
