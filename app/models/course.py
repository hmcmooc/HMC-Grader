# coding=utf-8

from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from mongoengine import NULLIFY, PULL

from app.filestorage import *

from app.models.user import User


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
  #bookkeeping
  problem = db.ReferenceField('Problem')
  isLatest = db.BooleanField(default=True)

  submissionTime = db.DateTimeField(required=True)
  isLate = db.BooleanField(default=False)
  grade = db.ReferenceField('GBGrade')
  status = db.IntField(default=0)
  gradedBy = db.ReferenceField('User')

  # 0 = Ungraded
  # 1 = Autograde inprogress
  # 2 = Autograde complete
  # 3 = Manual grading in progress
  # 4 = Manual grade complete
  comments = db.StringField(default="")

  partnerInfo = db.ReferenceField("PartnerInfo", reverse_delete_rule=NULLIFY, default=None)

  meta = {"cascade": True}

  def cleanup(self):
    try:
      if self.partnerInfo:
        self.partnerInfo.delete()
      self.grade.delete()
    except:
      pass

  def getStatus(self):
    if self.status == 0:
      return "info", "Submitted (Ungraded)"
    elif self.status == 1:
      return "warning", "Autograde in progress"
    elif self.status == 2:
      return "info", "Submitted (Tested, Ungraded)"
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

  def addSubmission(self, sub):
    if len(self.submissions) > 0:
      self.submissions[-1].isLatest = False
      self.submissions[-1].save()
    self.submissions.append(sub)

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

  #URLs for grader notes and for problem specification
  gradeNotes = db.StringField()
  problemPage = db.StringField()

  requiredFiles = db.StringField()

  #Map usernames to submission lists
  studentSubmissions = db.MapField(db.EmbeddedDocumentField('StudentSubmissionList'))

  meta = {"cascade": True}

  def __init__(self, name, **data):
    super(Problem, self).__init__(**data)
    self.name = name

  def getStatusCount(self):
    c,a = self.getParents()
    users = User.objects.filter(courseStudent=c)
    ungraded = 0
    ip = 0
    done = 0
    for u in users:
      sub = self.getLatestSubmission(u)
      if sub == None or sub.status < 3:
        ungraded += 1
      elif sub.status == 3:
        ip += 1
      else:
        done += 1
    return ungraded, ip, done

  def cleanup(self):
    if self.gradeColumn != None:
      self.gradeColumn.cleanup()
      self.gradeColumn.delete()
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

  def getFiles(self, user, subnum):
    from os import listdir
    from os.path import isfile, join
    c, a = self.getParents()
    filePath = getSubmissionPath(c, a, self, user, subnum)
    return [ f for f in listdir(filePath) if isfile(join(filePath,f)) ]

  def getRequiredFiles(self):
    import re
    if self.requiredFiles != None and len(self.requiredFiles) > 0:
      return re.split(', *', self.requiredFiles)
    else:
      return []

  def getSubmissionInfo(self, sub):
    for key, value in self.studentSubmissions.iteritems():
      if sub in value.submissions:
        return User.objects.get(username=key), (value.submissions.index(sub)+1)
    return None, -1


class AssignmentGroup(db.Document):
  '''
  A logical grouping of problems (e.g. One week's homework)
  '''
  name = db.StringField(required=True)
  gradeEntry = db.ReferenceField('GBGroup', reverse_delete_rule=NULLIFY)
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
  #Map real usernames to identifiers
  anonIds = db.MapField(db.StringField())
  #How do we calculate late grades (Defaults to one that just highlights late grades)
  lateGradePolicy = db.StringField(default="Highlighter")

  homepage = db.StringField(default="#")

  meta = {"cascade": True, 'ordering': ["+semester", "+name"]}

  def cleanup(self):
    self.gradeBook.cleanup()

    for a in self.assignments:
      a.cleanup()
      a.delete()

  def ensureIDs(self):
    users = User.objects.filter(courseStudent=self)
    for u in users:
      if u.username in self.anonIds:
        continue
      else:
        from random import choice, randint
        from string import ascii_lowercase
        while True:
          ID = choice(ascii_lowercase) + choice(ascii_lowercase)+ str(randint(0,9))
          if not ID in self.anonIds.values():
            self.anonIds[u.username] = ID
            break
    self.save()

  def getIdentifier(self, username):
    if not username in self.anonIds:
      self.ensureIDs()
    return self.anonIds[username]
