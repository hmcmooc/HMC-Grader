# -*- coding: utf-8 -*-

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for, flash, send_file
from flask.ext.login import login_user, logout_user, current_user, login_required

from flask.ext.mongoengine import DoesNotExist

from werkzeug import secure_filename

from models import *
from forms import SubmitAssignmentForm

import os, datetime

@app.route('/assignments/<cid>')
@login_required
def studentAssignments(cid):
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
def uploadFiles(cid, aid, pid):
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

        #TODO: Possibly reorder path
        filepath = os.path.join(app.config['GROODY_HOME'],c.semester,c.name,a.name,p.name,g.user.username)

        #Check for the metasubmission entry and create it if it doesn't exist
        if g.user.username not in p.studentSubmissions:
          p.studentSubmissions[g.user.username] = StudentSubmissionList()

        #Create a new grade entry in the gradebook
        grade = GBGrade()
        grade.save()
        p.gradeColumn.scores[g.user.username] = grade

        #Finish the filepath
        filepath = os.path.join(filepath, str(len(p.studentSubmissions[g.user.username].submissions)+1))

        #Make a new submission for the submission list
        sub = Submission()
        #Initial fields for submission
        sub.filePath = filepath
        sub.grade = p.gradeColumn.scores[g.user.username]
        sub.submissionTime = datetime.datetime.utcnow()

        sub.save()
        p.studentSubmissions[g.user.username].submissions.append(sub)

        #TODO handle partners

        #Check for lateness
        if p.duedate < sub.submissionTime:
          sub.isLate = True

        #make sure the directory exists
        os.makedirs(filepath)


        for f in request.files.getlist("files"):
          filename = secure_filename(f.filename)
          if filename == "":
            continue
          f.save(os.path.join(filepath, filename))

        p.save()
        p.gradeColumn.save()

    return redirect(url_for('studentAssignments', cid=cid))
  except (Course.DoesNotExist):
    raise e

@app.route('/assignments/download/<pid>/<uid>/<subnum>/<filename>')
@login_required
def downloadFiles(pid, uid, subnum, filename):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.courseStudent):
      return redirect(url_for('index'))

    u = User.objects.get(id=uid)

    s = p.getSubmission(u, subnum)

    return send_file(os.path.join(s.filePath, filename), as_attachment=True)
  except Course.DoesNotExist:
    pass
