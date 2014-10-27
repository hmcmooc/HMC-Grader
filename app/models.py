from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from mongoengine import NULLIFY, PULL


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

  def cleanup(self):
    for c in self.categories:
      c.cleanup()

class GBCategory(db.EmbeddedDocument):
  name = db.StringField(required=True)
  entries = db.ListField(db.ReferenceField('GBEntry'))

  def __init__(self, name, **data):
    super(GBCategory, self).__init__(**data)
    self.name = name

  def cleanup(self):
    for e in self.entries:
      e.cleanup()
      e.delete()

class GBEntry(db.Document):
  name = db.StringField(required=True)
  columns = db.ListField(db.ReferenceField('GBColumn'))

  def __init__(self, name, **data):
    super(GBEntry, self).__init__(**data)
    self.name = name

  def cleanup(self):
    for c in self.columns:
      c.cleanup()
      c.delete()

class GBColumn(db.Document):
  name = db.StringField()
  maxScore = db.DecimalField(default=0)

  #Map usernames to grade entries
  scores = db.MapField(db.ReferenceField('GBGrade'))


  def __init__(self, name, **data):
    super(GBColumn, self).__init__(**data)
    self.name = name

  def cleanup(self):
    # for k in self.scores:
    #   s = self.scores[k]
    #   self.scores[k] = None
    #   s.delete()
    pass

class GBGrade(db.Document):
  #Map score name (eg. GrutorScore or TestScore) to scores
  scores = db.MapField(db.DecimalField())
  visible = db.MapField(db.BooleanField())


'''
Course and submission models
'''

#TODO: Figure out what to do when a user is removed from a course
class PartnerInfo(db.Document):
  '''
  A database model for storing information about the partner of a specific
  submission
  '''
  user = db.ReferenceField('User')
  submission = db.ReferenceField('Submission')



class Submission(db.Document):
  submissionTime = db.DateTimeField(required=True)
  isLate = db.BooleanField(default=False)
  filePath = db.StringField(required=True)
  grade = db.ReferenceField('GBGrade')
  status = db.IntField(default=0)

  # 0 = Ungraded
  # 1 = Autograde inprogress
  # 2 = Autograde complete
  # 3 = Manual grading in progress
  # 4 = Manual grade complete
  comments = db.StringField(default="No Comments")

  partnerInfo = db.ReferenceField("PartnerInfo", reverse_delete_rule=NULLIFY, default=None)

  meta = {"cascade": True}

  def cleanup(self):
    try:
      if self.partnerInfo:
        self.partnerInfo.delete()
      self.grade.delete()
    except:
      pass

  def getFiles(self):
    from os import listdir
    from os.path import isfile, join
    return [ f for f in listdir(self.filePath) if isfile(join(self.filePath,f)) ]

  def getStatus(self):
    if self.status == 0:
      return "info", "Submitted (Ungraded)"
    elif self.status == 1:
      return "warning", "Autograde in progress"
    elif self.status == 2:
      return "info", "Submitted (Ungraded)"
    elif self.status == 3:
      return "warning", "Grading in progress"
    elif self.status == 4:
      return "success", "Graded"

class StudentSubmissionList(db.EmbeddedDocument):
  submissions = db.ListField(db.ReferenceField('Submission'))

  meta = {"cascade": True}

  def cleanup(self):
    for s in self.submissions:
      s.cleanup()
      s.delete()
    self.submissions = []

class Problem(db.Document):
  name = db.StringField()
  gradeColumn = db.ReferenceField('GBColumn', reverse_delete_rule=NULLIFY)
  duedate = db.DateTimeField()
  rubric = db.MapField(db.DecimalField())
  testfiles = db.ListField(db.StringField())
  allowPartners = db.BooleanField(default=True)

  #Map usernames to submission lists
  studentSubmissions = db.MapField(db.EmbeddedDocumentField('StudentSubmissionList'))

  meta = {"cascade": True}

  def __init__(self, name, **data):
    super(Problem, self).__init__(**data)
    self.name = name

  def cleanup(self):
    if self.gradeColumn != None:
      self.gradeColumn.cleanup()
    for k in self.studentSubmissions:
      self.studentSubmissions[k].cleanup()

  def totalPoints(self):
    total = 0
    for k in self.rubric:
      total += self.rubric[k]
    return total

  def getSubmissionNumber(self, user):
    '''gets the number of the latest submission'''
    if user.username in self.studentSubmissions:
      return len(self.studentSubmissions[user.username].submissions)
    else:
      return 0

  def getSubmission(self, user, subnum):
    '''Returns a single submission'''
    return self.studentSubmissions[user.username].submissions[int(subnum)-1]

  def getLatestSubmission(self, user):
    '''Gets the latest submission for a user'''
    if self.getSubmissionNumber(user) == 0:
      return None
    else:
      return self.getSubmission(user, self.getSubmissionNumber(user))

  def getParents(self):
    a = AssignmentGroup.objects.get(problems=self)
    c = Course.objects.get(assignments=a)
    return c,a

class AssignmentGroup(db.Document):
  name = db.StringField(required=True)
  gradeEntry = db.ReferenceField('GBEntry', reverse_delete_rule=NULLIFY)
  problems = db.ListField(db.ReferenceField('Problem', reverse_delete_rule=PULL))

  meta = {"cascade": True}

  def __init__(self, name, **data):
    super(AssignmentGroup, self).__init__(**data)
    self.name = name

  def cleanup(self):
    if self.gradeEntry != None:
      self.gradeEntry.cleanup()
    for p in self.problems:
      p.cleanup()
      p.delete()

class Course(db.Document):
  #Identification information
  name = db.StringField(required=True)
  semester = db.StringField(required=True)

  #Information for grading and submission
  gradeBook = db.EmbeddedDocumentField('GradeBook')
  assignments = db.ListField(db.ReferenceField('AssignmentGroup', reverse_delete_rule=PULL))

  #Is this course still being taught at this time
  isActive = db.BooleanField(default=True)

  meta = {"cascade": True, 'ordering': ["+semester", "+name"]}

  def cleanup(self):
    self.gradeBook.cleanup()

    for a in self.assignments:
      a.cleanup()
      a.delete()

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
  courseStudent    = db.ListField(db.ReferenceField('Course', reverse_delete_rule=PULL))
  courseGrutor     = db.ListField(db.ReferenceField('Course', reverse_delete_rule=PULL))
  courseInstructor = db.ListField(db.ReferenceField('Course', reverse_delete_rule=PULL))

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
