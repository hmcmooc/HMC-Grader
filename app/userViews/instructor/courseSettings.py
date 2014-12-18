# coding=utf-8

'''This module handles all functions responsible for modifying the course
settings page.

View Function: instructorCourseSettings (instructor/courseSettings.html)

Redirect Functions: TODO

AJAX Fuctions: TODO
'''

#Import the app
from app import app

#Import needed flask functions
from flask import g, render_template, redirect, url_for, flash, jsonify, abort
from flask import request
from flask.ext.login import current_user, login_required

#Import the models we need on these pages
from app.structures.models.user import *
from app.structures.models.gradebook import *
from app.structures.models.course import *

#Import the forms needed on these pages
from app.structures.forms import CreateAssignmentForm, AddUserCourseForm
from app.structures.forms import CourseSettingsForm

#Import app helpers
from app.helpers.filestorage import *

#Import app helper functions
from app.plugins.latework import getLateCalculators
import shutil, random, string

@app.route('/editcourse/<cid>')
@login_required
def instructorCourseSettings(cid):
  '''
  Function Type: View Function
  Template: instructor/courseSettings.html
  Purpose: Allows an instructor to manipulate the assignemnts of a course.
  Course settings, and the users and graders for a course.

  Inputs:
    cid: The object ID of the course being administered

  Template Parameters:
    course: The course specified by <cid> to be administered
    students: A list of user objects who are enrolled as students
    grutors: A list of user objects who are enrolled as grutors
    instrs: A list of user objects who are enrolled as instructorSaveSettings
    guserform: An AddUserCourseForm for adding grutors
    suserform: An AddUserCourseForm for adding students
    iuserform: An AddUserCourseForm for adding instructors
    settingsForm: A CourseSettingsForm for changing the settings of the course

  Forms Handled: None
  '''
  try:
    c = Course.objects.get(id=cid)
    if not c in current_user.courseInstructor:
      abort(403)

    #Get the users for this course
    s = User.objects.filter(courseStudent=c)
    grutor = User.objects.filter(courseGrutor=c)
    i = User.objects.filter(courseInstructor=c)

    settingsForm = CourseSettingsForm()

    lateCalculators = getLateCalculators()

    settingsForm.latePolicy.choices = [(x,x) for x in lateCalculators.keys()]

    #Make sure all users have anonIds
    if c.anonymousGrading:
      c.ensureIDs()

    #TODO: Refactor forms to use javascript/AJAX
    return render_template("instructor/courseSettings.html",\
     course=c, students=s, grutors=grutor, instrs=i,\
     form=CreateAssignmentForm(), suserform=AddUserCourseForm(),\
     guserform=AddUserCourseForm(), iuserform=AddUserCourseForm(),
     settingsForm=settingsForm)
  except Course.DoesNotExist:
    return abort(404)

@app.route('/assignment/<cid>/settings', methods=['POST'])
@login_required
def instructorSaveCourseSettings(cid):
  '''
  Function Type: Callback-AJAX Function
  Called By: instructor/course.html:saveSettings()
  Purpose: Recieves the current state of the settings form and applies those
  settings to the course.

  Inputs:
    cid: The object ID of the course to apply the settings to

  POST Values: A dictionary of settings names to values

  Outputs:
    res: True if the operation succeeded otherwise False
  '''
  try:
    c = Course.objects.get(id=cid)
    if not c in g.user.courseInstructor:
      return jsonify(status=403), 403

    content = request.get_json()
    c.anonymousGrading = content['anonymousGrading']
    c.lateGradePolicy = content['lateGradePolicy']
    c.homepage = content['homepage']
    c.save()
    return jsonify(res=True)
  except Exception as e:
    return jsonify(res=False, msg=str(e))

#
# Assignment creation and deletion
#

@app.route('/assignment/<cid>/create', methods=['POST', 'GET'])
@login_required
def instructorCreateAssignmentGroup(cid):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Creates a new assignment group with information specified in
  the CreateAssignmentForm.

  Inputs:
    cid: The object ID of the course to add the assignment group to

  Forms Handled:
    CreateAssignmentForm: Verify that an assignment of the same name doesn't
    already exists and then create a new assignment in the course specified by
    <cid>.
  '''
  if request.method == "POST":
    form = CreateAssignmentForm(request.form)
    if form.validate():
      try:
          c = Course.objects.get(id=cid)
          #For security purposes we send anyone who isnt an instructor or
          #admin away
          if not c in current_user.courseInstructor:
            abort(403)

          #If this assignment already exists we want to return now
          if form.name.data in c.assignments:
            flash("Assignment Group already exists")
            return redirect(url_for('instructorCourseSettings', id=cid))


          #Create the assignment and problem
          a = AssignmentGroup(form.name.data)
          a.save()
          c.assignments.append(a)

          #Create a GBEntry and GBColumn
          e = GBGroup(form.name.data)
          e.save()
          c.gradeBook.assignmentGrades.append(e)
          #Give the assignment its entry
          a.gradeEntry = e

          #Make sure there is a location on the drive to store this
          ensurePathExists(getAssignmentPath(c,a))

          #Save the documents
          a.save()
          c.save()
          flash("Added Assignment Group")
          return redirect(url_for('instructorCourseSettings', cid=cid))
      except Course.DoesNotExist as e:
        abort(404)
  return redirect(url_for('instructorCourseSettings', cid=cid))

@app.route('/assignment/<cid>/<aid>/del')
@login_required
def instructorDeleteAssignmentGroup(cid, aid):
  '''
  Function Type: Callback-AJAX Function
  Purpose: Delete an assignment and all problems in that assignment.

  Inputs:
    cid: The object ID of the course the assignment is in
    aid: The object ID of the assignment group to add the problem to

  Forms Handled: None
  '''
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not c in g.user.courseInstructor:
      return jsonify(status=403), 403


    a = AssignmentGroup.objects.get(id=aid)

    #Remove the filestorage
    randString = ''.join(random.choice(string.letters + string.digits) for _ in range(10))
    assignPath = getAssignmentPath(c, a)
    shutil.move(assignPath, assignPath+'_'+randString)

    c.assignments.remove(a)

    c.gradeBook.assignmentGrades.remove(a.gradeEntry)

    a.gradeEntry.cleanup()
    a.gradeEntry.delete()
    a.cleanup()
    a.delete()
    c.save()
  except Course.DoesNotExist:
    return jsonify(status=404), 404
  except AssignmentGroup.DoesNotExist:
    pass
  return jsonify(status=200)

#
# Functions for adding and removing problems
#

@app.route('/assignment/<cid>/<aid>/addproblem')
@login_required
def instructorAddProblem(cid,aid):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Add a problem to the specified assignment in a course. When
  added it redirects to a page to edit the problem settings.

  Inputs:
    cid: The object ID of the course the assignment is in
    aid: The object ID of the assignment group to add the problem to

  Forms Handled: None
  '''
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not current_user.courseInstructor:
      abort(403)

    a = AssignmentGroup.objects.get(id=aid)

    problemNumber = len(a.problems)
    #default problem name
    problemName = "Problem " + str(problemNumber)

    p = Problem(problemName)
    p.save()

    gc = GBColumn(problemName)
    gc.save()

    p.gradeColumn = gc
    p.save()

    #Put the problem in the assignment
    a.problems.append(p)
    a.save()

    #Put the column in the gradebook
    a.gradeEntry.columns.append(gc)
    a.gradeEntry.save()

    #Create the storage space for the problem and its tests
    ensurePathExists(getProblemPath(c,a,p))
    ensurePathExists(getTestPath(c,a,p))

    flash("This is your first time creating the problem please fill in all the form fields an hit save")
    return redirect(url_for('instructorProblemSettings', pid=p.id))
  except Course.DoesNotExist:
    abort(404)

@app.route('/assignment/<cid>/<aid>/remproblem/<pid>')
@login_required
def instructorDeleteProblem(cid,aid,pid):
  '''
  Function Type: Callback-AJAX Function
  Purpose: Remove a problem from a specified assignment.

  Inputs:
    cid: The object ID of the course the assignment is in
    aid: The object ID of the assignment group to add the problem to
    pid: The object ID of the problem to remove

  Forms Handled: None
  '''
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in g.user.courseInstructor):
      return jsonify(status=403), 403

    a = AssignmentGroup.objects.get(id=aid)
    p = Problem.objects.get(id=pid)

    #Remove storage space
    randString = ''.join(random.choice(string.letters + string.digits) for _ in range(10))
    probPath = getProblemPath(c, a, p)
    shutil.move(probPath, probPath+'_'+randString)
    #removePath(getProblemPath(c, a, p))

    #We leverage mongo's reverse delete rules to remove the problem from the
    #assignment's problem list

    p.cleanup()
    p.delete()

    return jsonify(status=200)
  except (Course.DoesNotExist, AssignmentGroup.DoesNotExist, Problem.DoesNotExist):
    return jsonify(status=404), 404


#
# Functions for adding and removing users
#

@app.route('/editcourse/<cid>/adduser', methods=['POST'])
@login_required
def instructorAddUserToCourse(cid):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Add a user to the specified course. What type of user (Student,
  grutor, or instructor) is determined by the value of the submit button of the
  form.

  Inputs:
    cid: The object ID of the course to add the user to

  Forms Handled:
    AddUserCourseForm: Read in the username and determine which type of user
    based on the value of the submit button.
  '''
  try:
    c = Course.objects.get(id=cid)

    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not c in current_user.courseInstructor:
      abort(403)

    if request.method == "POST":
      form = AddUserCourseForm(request.form)
      if form.validate():
        u = User.objects.get(username=form.uname.data)
        if request.form['btn'] == "student":
          u.courseStudent.append(c)
        elif request.form['btn'] == "grutor":
          u.courseGrutor.append(c)
        else:
          u.courseInstructor.append(c)
        u.save()
  except User.DoesNotExist:
    flash("Failed to find user", "error")
  except Course.DoesNotExist:
    abort(404)
  return redirect(url_for('instructorCourseSettings', cid=cid))

@app.route('/editcourse/<cid>/remuser/<uid>/<t>')
@login_required
def instructorRemoveUserFromCourse(cid, uid, t):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Remove a user of the specified type from the course.

  Inputs:
    cid: The object ID of the course to remove the user from
    uid: The object ID of the user to remove
    t: The type of user (Student, Grutor, Instructor) to remove the user from

  Forms Handled: None
  '''
  try:
    c = Course.objects.get(id=cid)

    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not c in current_user.courseInstructor:
      abort(403)


    u = User.objects.get(id=uid)
    if t == "student":
      u.courseStudent.remove(c)
    elif t == "grutor":
      u.courseGrutor.remove(c)
    else:
      u.courseInstructor.remove(c)
    u.save()

  except User.DoesNotExist:
    flash("Failed to find user")
  except Course.DoesNotExist:
    abort(404)
  return redirect(url_for('administerCourse', cid=cid))
