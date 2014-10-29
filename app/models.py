from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from mongoengine import NULLIFY, PULL

class GradeBook(db.EmbeddedDocument):
  '''
  The gradebook class is designed to contain all the information regarding
  grades for a course. Each Course has one Gradebook. A gradebook can be
  divided into Categories which contain Entries and then Columns. This is to
  facilitate good layout of the information.
  '''
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
  '''
  A category is designed to group common items together (eg assignments,
  participation, tests)
  '''
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
  '''
  Entries are designed to contain columns that are temporall related. Such as
  all of the problems in a certain week. (This level of granularity isn't
  accessible in the manual gradebook, this may be a source of a refactor)
  '''
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

class GBGrade(db.Document):
  '''
  A grade contains a dictionary mapping rubric sections to scores. Additionally
  it contains booleans which determines if a score is supposed to be visible yet
  (This may be factored out as it is redundant with the status of the
  student's submission)
  '''
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
  '''
  A submission contains all the information about one attempt at a given problem
  by a student.
  '''
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

  #TODO: Don't store absolute path
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
  '''
  A list of all the submissions a student has made for a specific problem.
  '''
  submissions = db.ListField(db.ReferenceField('Submission'))

  meta = {"cascade": True}

  def cleanup(self):
    for s in self.submissions:
      s.cleanup()
      s.delete()
    self.submissions = []

class Problem(db.Document):
  '''
  One problem that a student can submit files to.
  '''
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
  '''
  A logical grouping of problems (e.g. One week's homework)
  '''
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
  '''
  One sememsters class
  '''
  #Identification information
  name = db.StringField(required=True)
  semester = db.StringField(required=True)

  #Information for grading and submission
  gradeBook = db.EmbeddedDocumentField('GradeBook')
  assignments = db.ListField(db.ReferenceField('AssignmentGroup', reverse_delete_rule=PULL))

  #Is this course still being taught at this time
  isActive = db.BooleanField(default=True)

  #Do we show usernames during grading
  anonymousGrading = db.BooleanField(default=False)

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
  '''
  The information for one user of the system (Student, Grader, or Instructor)
  '''
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
