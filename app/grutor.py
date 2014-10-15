# -*- coding: utf-8 -*-

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for, flash, send_file, jsonify
from flask.ext.login import login_user, logout_user, current_user, login_required

from flask.ext.mongoengine import DoesNotExist

from werkzeug import secure_filename

from models import *
from forms import SubmitAssignmentForm

import os, datetime
import markdown

@app.route('/grutor/assignments/<cid>')
@login_required
def grutorAssignments(cid):
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.gradingCourses()):
      return redirect(url_for('index'))

    return render_template("grutor/assignments.html", course=c)
  except Exception as e:
    raise e

@app.route('/grutor/gradelist/problem/<pid>')
@login_required
def grutorGradelistProblem(pid):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.gradingCourses()):
      return redirect(url_for('index'))

    #Get the students for this course
    students = User.objects.filter(courseStudent=c)

    return render_template("grutor/problems.html", \
                            course=c, problem=p, assignment=a, users=students)
  except Exception as e:
    raise e

@app.route('/grutor/grade/<pid>/<uid>/<subnum>')
@login_required
def grutorGradeSubmission(pid, uid, subnum):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    user = User.objects.get(id=uid)

    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.gradingCourses()):
      return redirect(url_for('index'))

    #p = Problem.objects.get(id=pid)
    #a = AssignmentGroup.objects.get(id=aid)

    submission = p.getSubmission(user, subnum)
    submission.status = max(submission.status, 3)

    if submission.partnerInfo != None:
      submission.partnerInfo.submission.status = max(submission.partnerInfo.submission.status, 3)
      submission.partnerInfo.submission.save()

    submission.save()

    p.save()

    return render_template("grutor/gradesubmission.html", \
                            course=c, problem=p, assignment=a, subnum=subnum,
                            user=user, submission=submission)
  except Exception as e:
    raise e


@app.route('/grutor/finish/<pid>/<uid>/<subnum>')
@login_required
def grutorFinishSubmission(pid, uid, subnum):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    user = User.objects.get(id=uid)

    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.gradingCourses()):
      return redirect(url_for('index'))

    #Define a function for performing closing operations
    def finish(sub):
      sub.status = max(sub.status, 4)
      for g in sub.grade.scores:
        sub.grade.visible[g] = True

      sub.grade.save()
      sub.save()
    #End definition

    submission = p.getSubmission(user, subnum)
    finish(submission)

    #Handle the partners submission as well
    #TODO: Make this a function for cleaner code
    if submission.partnerInfo != None:
      finish(submission.partnerInfo.submission)

    p.save()

    return redirect(url_for('grutorGradelistProblem', pid=pid))
  except Exception as e:
    raise e

@app.route('/grutor/release/<pid>/<uid>/<subnum>')
@login_required
def grutorReleaseSubmission(pid, uid, subnum):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    user = User.objects.get(id=uid)

    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.gradingCourses()):
      return redirect(url_for('index'))

    #Define function for releasing submissions
    def release(sub):
      sub.status = min(submission.status, 2)
      sub.grade.save()
      sub.save()
    #End definition

    submission = p.getSubmission(user, subnum)
    #if not submission.status == 4:
    release(submission)

    if submission.partnerInfo != None:
      release(submission.partnerInfo.submission)

    p.save()

    return redirect(url_for('grutorGradelistProblem', pid=pid))
  except Exception as e:
    raise e

'''
Function to create a blank submission
'''

@app.route('/grutor/create/<pid>/<uid>')
@login_required
def grutorMakeBlank(pid, uid):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()
    user = User.objects.get(id=uid)

    #For security purposes we send anyone who isnt in this class to the index
    if not (c in current_user.gradingCourses()):
      return redirect(url_for('index'))

    #Check that the user we are trying to create a submission for is in the class
    if not (c in user.courseStudent):
      return redirect(url_for('index'))

    #Create a blank submission
    #Create the grade
    grade = GBGrade()
    grade.save()
    p.gradeColumn.scores[user.username] = grade


    p.studentSubmissions[user.username] = StudentSubmissionList()

    #create a filepath
    filepath = os.path.join(app.config['GROODY_HOME'],c.semester,c.name,a.name,p.name,user.username)
    filepath = os.path.join(filepath, str(len(p.studentSubmissions[g.user.username].submissions)+1))

    sub = Submission()
    #Initial fields for submission
    sub.filePath = filepath
    sub.grade = p.gradeColumn.scores[user.username]
    sub.submissionTime = datetime.datetime.utcnow()

    sub.save()
    p.studentSubmissions[user.username].submissions.append(sub)


    #TODO handle partners
    #The grader is making this so it isn't late
    sub.isLate = False

    #Create the needed folders
    os.makedirs(filepath)

    p.save(cascade=True)
    return redirect(url_for('grutorGradeSubmission', uid=uid, pid=pid, subnum=1))
  except Course.DoesNotExist as e:
    raise e



'''
Callbacks for Javascript
'''

@app.route('/grutor/grade/<pid>/<uid>/<subnum>/savegrade', methods=['POST'])
@login_required
def grutorSaveGrades(pid, uid, subnum):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()

    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.gradingCourses()):
      return jsonify(res=False)

    #Try to get the contents
    content = request.get_json()

    #make sure we got the contents
    if content == None:
      return jsonify(res=False)

    #Define function for applying scores to a submission
    def score(sub):
      for section in content:
        sub.grade.scores[section] = content[section]

      sub.grade.save()
      sub.save()
    #End definition

    user = User.objects.get(id=uid)
    sub = p.getSubmission(user, subnum)

    score(sub)
    if sub.partnerInfo != None:
      score(sub.partnerInfo.submission)

    return jsonify(res=True)

  except Exception as e:
    return jsonify(res="Exception raised: "+ str(e))

@app.route('/grutor/grade/preview', methods=['POST'])
@login_required
def grutorPreview():
  content = request.get_json()
  html = markdown.markdown(content["text"])
  return jsonify(res=html)

@app.route('/grutor/grade/<pid>/<uid>/<subnum>/savecomment', methods=['POST'])
@login_required
def grutorSaveComment(pid, uid, subnum):
  try:
    p = Problem.objects.get(id=pid)
    c,a = p.getParents()

    #For security purposes we send anyone who isnt in this class to the index
    if not ( c in current_user.gradingCourses()):
      return jsonify(res=False)

    #Try to get the contents
    content = request.get_json()

    #make sure we got the contents
    if content == None:
      return jsonify(res=False)

    #Define function for saving comments
    def comment(sub):
      sub.comments = content['text']
      sub.save()

    user = User.objects.get(id=uid)
    sub = p.getSubmission(user, subnum)

    comment(sub)
    if sub.partnerInfo != None:
      comment(sub.partnerInfo.submission)


    #Save changes to the problem
    p.save(cascade=True)

    return jsonify(res=True)

  except Exception as e:
    return jsonify(res="Exception raised: "+ str(e))
