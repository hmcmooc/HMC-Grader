# -*- coding: utf-8 -*-

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for, flash, send_file
from flask.ext.login import login_user, logout_user, current_user, login_required

from flask.ext.mongoengine import DoesNotExist

from werkzeug import secure_filename

from models import *
from forms import SubmitAssignmentForm
from autograde import gradeSubmission

from app.filestorage import *
from app.latework import getLateCalculators

import os, datetime

@app.route('/assignments/<cid>')
@login_required
def studentAssignments(cid):
  '''
  Function Type: View Function
  Template: student/assignments.html
  Purpose: Display to a student user all of the assignments which they can
  submit homework to.

  Inputs:
    cid: The object ID for the course the student is viewing

  Template Parameters:
    course: The Course object given by <cid>

  Forms Handled: None
  '''
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.courseStudent):
      return redirect(url_for('index'))

    return render_template("student/assignments.html", course=c)
  except Exception as e:
    raise e

@app.route('/assignments/submit/<pid>')
@login_required
def submitAssignment(pid):
  '''
  Function Type: View Function
  Template: student/submit.html
  Purpose: Allow a student to submit files for a homework assignment problem.

  Inputs:
    pid: The object ID for the problem being submitted to

  Template Parameters:
    course: The course which contains the problem
    assignment: The assignment group containing the problem
    problem: The problem object specified by <pid>
    form: A SubmitAssignmentForm which has had the partner field filled with
    the students from course.

  Forms Handled: None
  '''
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.courseStudent):
      return redirect(url_for('index'))

    saf = SubmitAssignmentForm()
    saf.partner.choices = [("None", "None")] + [(str(x.id), x.username) for x in User.objects.filter(courseStudent=c) if not x.username == current_user.username]

    return render_template("student/submit.html", \
                            course=c, assignment=a, problem=p,\
                            form=saf)
  except Exception as e:
    raise e

@app.route('/assignments/view/<pid>/<subnum>')
@login_required
def viewProblem(pid,subnum):
  '''
  Function Type: View Function
  Template: student/viewsubmission.html
  Purpose: Allow a student to view their submission and feedback from the
  autograder and the student graders.

  Inputs:
    pid: The object ID of the problem that this submission belongs to
    subnum: Which submission by the student should be viewed

  Template Parameters:
    course: The course which contains the problem
    assignment: The assignment group containing the problem
    problem: The problem object specified by <pid>
    subnum: The number of the current submission
    submission: The Submission object for this submission

  Forms Handled: None
  '''
  try:
    p = Problem.objects.get(id=pid)
    c, a = p.getParents()
    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.courseStudent):
      return redirect(url_for('index'))

    submission = p.getSubmission(current_user, subnum)

    return render_template("student/viewsubmission.html", \
                            course=c, assignment=a, problem=p,\
                             subnum=subnum, submission=submission)
  except Course.DoesNotExist:
    pass
  return redirect(url_for('studentAssignments', cid=cid))

'''
Backend upload/download functions
'''

@app.route('/assignments/submit/<pid>/upload', methods=['POST'])
@login_required
def uploadFiles(pid):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Create a new submission and put the files in the backing filesystem.
  If a partner is specified create the partner's submission as well and link the
  two submissions.

  Inputs:
    pid: The object ID for the problem to be submitted to.

  Forms Handled:
    SubmitAssignmentForm: Contains the files being submitted and the partner
    choice.
  '''
  try:
    p = Problem.objects.get(id=pid)
    c, a = p.getParents()
    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.courseStudent):
      return redirect(url_for('index'))

    if request.method == "POST":
      form = SubmitAssignmentForm(request.form)
      form.partner.choices = [("None", "None")] + [(str(x.id), x.username) for x in User.objects.filter(courseStudent=c) if not x.username == current_user.username]
      if form.validate():
        filepath = getProblemPath(c, a, p)
        userSub = createSubmission(p, g.user, filepath, request.files.getlist("files"))

        if form.partner.data != "None":
          partner = User.objects.get(id=form.partner.data)
          partnerSub = createSubmission(p, partner, filepath, request.files.getlist("files"))

          #Create the partner info for the first user
          uPartnerInfo = PartnerInfo()
          uPartnerInfo.user = partner
          uPartnerInfo.submission = partnerSub
          uPartnerInfo.save()
          userSub.partnerInfo = uPartnerInfo

          #Create the partner info for the partner
          pPartnerInfo = PartnerInfo()
          pPartnerInfo.user = User.objects.get(id=g.user.id)
          pPartnerInfo.submission = userSub
          pPartnerInfo.save()
          partnerSub.partnerInfo = pPartnerInfo

          #Save the submissions
          userSub.save()
          partnerSub.save()

        p.save()
        p.gradeColumn.save()


        #Grade after everything is saved
        gradeSubmission.delay(p.id, g.user.id, p.getSubmissionNumber(g.user))
        if form.partner.data != "None":
          gradeSubmission.delay(p.id, partner.id, p.getSubmissionNumber(partner))

    return redirect(url_for('studentAssignments', cid=c.id))
  except (Course.DoesNotExist):
    raise e

def createSubmission(problem, user, filepath, files):
  '''
  Function Type: Helper Function
  Purpose: Creates a new submission for a specified User.

  Inputs:
    problem: The problem object for this submission
    user: The user object for the user this submission is for
    filepath: The storage location for the files (To be removed)
    files: A list of files to be added to this assignment
  '''
  filepath = os.path.join(filepath, user.username)
  #Check for the metasubmission entry and create it if it doesn't exist
  if user.username not in problem.studentSubmissions:
    problem.studentSubmissions[user.username] = StudentSubmissionList()

  #Create a new grade entry in the gradebook
  grade = GBGrade()
  grade.save()
  problem.gradeColumn.scores[user.username] = grade

  #Finish the filepath
  filepath = os.path.join(filepath, str(len(problem.studentSubmissions[g.user.username].submissions)+1))

  #Make a new submission for the submission list
  sub = Submission()
  #Initial fields for submission
  sub.grade = problem.gradeColumn.scores[user.username]
  sub.submissionTime = datetime.datetime.utcnow()

  sub.save()
  problem.studentSubmissions[user.username].submissions.append(sub)

  #Check for lateness
  if problem.duedate < sub.submissionTime:
    sub.isLate = True

  #make sure the directory exists
  os.makedirs(filepath)


  for f in files:
    filename = secure_filename(f.filename)
    if filename == "":
      continue
    f.save(os.path.join(filepath, filename))

  sub.save()

  return sub

@app.route('/assignments/download/<pid>/<uid>/<subnum>/<filename>')
@login_required
def downloadFiles(pid, uid, subnum, filename):
  '''
  Function Type: Callback-Download
  Purpose: Downloads the file specified for the user.

  Inputs:
    pid: The object ID of the problem that the file belongs to
    uid: The object ID of the user the file belongs to
    subnum: The submission number that the file belongs to
    filename: The filename from the submission to download
  '''
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.courseStudent or c in current_user.gradingCourses()):
      return redirect(url_for('index'))

    u = User.objects.get(id=uid)

    s = p.getSubmission(u, subnum)

    filepath = getSubmissionPath(c, a, p, u, subnum)

    return send_file(os.path.join(filepath, filename), as_attachment=True)
  except Course.DoesNotExist:
    pass

@app.route('/grades')
@login_required
def viewGrades():
  '''
  Function Type: View Function
  Purpose: Show the user thier grades

  Inputs: None
  '''
  # from app.instructor.views import greateGradeLists, preventCollapse
  # import itertools
  #
  # lateCalculators = getLateCalculators()
  #
  # gradeLists = {}
  # #Create gradelists for all of courses
  # for c in g.user.courseStudent:
  #   gl = createGradeLists([g.user], c)[g.user.username]
  #   gl = lateCalulators[c.lateGradePolicy](gl)
  #   gl = preventCollapse(gl)
  #   gl = list(itertools.chain.fromIterable(gl))
  #   gradeLists[c.id] = gl
