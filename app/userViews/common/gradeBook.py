# coding=utf-8

'''
This module handles rendering the gradebook and its associated functions such
as download and handling rendering rows of the table
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

#Import forms for this page
from app.structures.forms import CreateGradeColumnForm, CreateGradebookGroupForm

#Import app helpers
from app.helpers.gradebook import getStudentAssignmentScores, getStudentAuxScores

@app.route('/gradebook/<cid>/<bool:instr>')
@login_required
def viewGradebook(cid, instr):
  '''
  Function Type: View Function
  Template: instructor/gradebook.html
  Purpose: Display all of the grades for this course. Allow for creation of
  arbitrary submission entries.

  Inputs:
    cid: The object ID of the course to display

  Template Parameters: TODO

  Forms Handled: TODO
  '''
  try:
    c = Course.objects.get(id=cid)
    if instr and not c in current_user.courseInstructor:
      abort(403)
    elif not instr and not c in current_user.gradingCourses():
      abort(403)

    #Get the users for this course
    s = User.objects.filter(courseStudent=c)


    disableColForm = False
    colForm = CreateGradeColumnForm()
    colForm.group.choices = [(x.id,x.name) for x in c.gradeBook.auxillaryGrades]
    if len(colForm.group.choices) == 0:
      colForm.group.choices = [("N/A", "N/A")]
      disableColForm = True


    s = list(s)
    s.sort(key=lambda x:x.username)
    uids = [str(u.id) for u in s]

    return render_template('common/gradebook.html', course=c, uids=uids,\
                      groupForm=CreateGradebookGroupForm(),\
                      colForm=colForm, disableColForm=disableColForm,\
                      instructor=instr)
  except Course.DoesNotExist:
    abort(404)

def createHighlight(gradeSpec):
  if 'highlight' in gradeSpec:
    if gradeSpec['highlight'] == 'red':
      return "class='danger'"
    elif gradeSpec['highlight'] == 'yellow':
      return "class='warning'"
    elif gradeSpec['highlight'] == 'blue':
      return "class='info'"
    elif gradeSpec['highlight'] == 'green':
      return "class='success'"
  else:
    return ""

@app.route('/gradebook/<cid>/<bool:instr>/renderGrade', methods=['POST'])
@login_required
def commonRenderGrade(cid, instr):
  try:
    content = request.get_json()
    c = Course.objects.get(id=cid)
    u = User.objects.get(id=content['uid'])

    if not c in current_user.gradingCourses():
      abort(403)

    assignmentScores = getStudentAssignmentScores(c, u)

    userCourseScore = 0

    outString = "<tr>"
    # <td>{{username/identifier}}</td>
    outString += "<td>"
    if instr:
      outString += u.username
      if c.anonymousGrading:
        outString += " (" + c.getIdentifier(u.username) + ")"
    else:
      if c.anonymousGrading:
        outString += c.getIdentifier(u.username)
      else:
        outString += u.username
    outString += "</td>"
    # <td>{{link to problem grading}}</td>
    for assignment, a in zip(assignmentScores, c.assignments):
      #If this assignment doesn't have any problems we put a blank column in
      if len(assignment) == 0:
        outString += "<td class='active'></td>"
        continue

      for problem, p in zip(assignment, a.problems):
        if problem == None:
          #If there was no submission link to the make blank page
          outString += "<td class='active'><a href='"
          outString += "#'" #TODO Replace this with an actual link
          outString += ">0.00/%.2f"%(p.gradeColumn.maxScore)
          outString += "</a></td>"
        else:
          highlight = createHighlight(problem)
          url = url_for('grutorGradeSubmission', pid=p, uid=u.id, subnum=p.getSubmissionNumber(u))
          if 'finalTotalScore' in problem:
            points =  p['finalTotalScore']
            userCourseScore += p['finalTotalScore']
          else:
            points = p['rawTotalScore']
            userCourseScore += p['rawTotalScore']

          maxPoints = p.gradeColumn.maxScore
          cellTemplate = "<td %s><a href='%s'>%.2f/%.2f</a></td>" % (highlight, url, points, maxPoints)
          outString += cellTemplate

    for group in c.gradeBook.auxillaryGrades:
      if len(group.columns) == 0:
        outString += "<td class='active'></td>"
        continue

      for col in group.columns:
        score = col.scores.setdefault(u.username, None)
        if score:
          outString += "<td>%.2f/%.2f</td>" % (score.totalScore(), col.maxScore)
          userCourseScore += score.totalScore()
        else:
          outString += "<td>%.2f/%.2f</td>" % (0, col.maxScore)

    outString += "<td>%.2f/%.2f</td></tr>" % (userCourseScore, c.gradeBook.totalPoints())
    return jsonify(res=outString)

  except (Course.DoesNotExist,User.DoesNotExist):
    abort(404)

@app.route('/gradebook/<cid>/addGroup', methods=['POST'])
@login_required
def addGradeGroup(cid):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Add a grade group to the gradebook for a course

  Inputs:
    cid: The object ID of the course to modify

  Forms Handled:
    CreateGradebookGroupForm: Reads in the name and creates that group if it
    doesn't already exist
  '''
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      abort(403)

    grades = c.gradeBook.auxillaryGrades

    if request.method == 'POST':
      form = CreateGradebookGroupForm(request.form)
      if form.validate():
        for grade in grades:
          if grade.name == form.groupName.data:
            flash("Group name already exists")
            return redirect(url_for('viewGradebook', cid=cid))

        group = GBGroup(form.groupName.data)
        group.save()
        c.gradeBook.auxillaryGrades.append(group)
        c.save()
        flash("Added group")
    return redirect(url_for('viewGradebook', cid=cid, instr=True))
  except Exception as e:
    raise e

@app.route('/gradebook/<cid>/addColumn', methods=['POST'])
@login_required
def addGradeColumn(cid):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Add a grade group to the gradebook for a course

  Inputs:
    cid: The object ID of the course to modify

  Forms Handled:
    CreateGradebookGroupForm: Reads in the name and creates that group if it
    doesn't already exist
  '''
  try:
    c = Course.objects.get(id=cid)
    #For security purposes we send anyone who isnt an instructor or
    #admin away
    if not (g.user.isAdmin or c in current_user.courseInstructor):
      abort(403)

    if request.method == 'POST':
      form = CreateGradeColumnForm(request.form)
      form.group.choices = [(unicode(x.id),x.name) for x in c.gradeBook.auxillaryGrades]

      if form.validate():
        group = GBGroup.objects.get(id=form.group.data)
        for c in group.columns:
          if c.name == form.name.data:
            flash("Column name already exists", "warning")
            return redirect(url_for('viewGradebook', cid=cid, instr=True))

        col = GBColumn(form.name.data)
        col.save()
        group.columns.append(col)
        group.save()
        flash("Group added")
    return redirect(url_for('viewGradebook', cid=cid, instr=True))
  except Exception as e:
    raise e

@app.route('/gradebook/<cid>/edit/<col>/<bool:instr>')
@login_required
def redirectGradebook(cid, col, instr):
  '''
  Function Type: Callback-Redirect Function
  Purpose: Given a gradebook column redirect to either the problem editing page
  or the column editing page depening on if the column is for a problem or just
  an arbitrary grade

  Inputs:
    cid: The object ID for the course that this column is in
    col: The object ID of the GBColumn that we are trying to redirect to

  Forms Handled: None
  '''
  c = Course.objects.get(id=cid)
  col = GBColumn.objects.get(id=col)
  for a in c.assignments:
    for p in a.problems:
      if p.gradeColumn == col:
        return redirect(url_for('grutorGradelistProblem', pid=p.id))

  return redirect(url_for('editAuxillaryGrades', cid=cid, instr=instr, col=col.id))


#
# We are lumping the gradebook column in here with the gradebook table
#

@app.route('/gradebook/<cid>/<bool:instr>/<col>')
@login_required
def editAuxillaryGrades(cid, instr, col):
  '''
  Function Type: View Function
  Template: instructor/editcolumn.html
  Purpose: Allows the grutor to edit one column of the gradebook manually

  Inputs:
    cid: The object ID of the course to authenticate the grader
    col: The object ID of the column to be edited

  Template Parameters: TODO
  '''
  try:
    course = Course.objects.get(id=cid)
    column = GBColumn.objects.get(id=col)

    if instr and not course in current_user.courseInstructor:
      abort(403)
    elif not instr and not course in current_user.gradingCourses():
      abort(403)

    users = User.objects.filter(courseStudent=course)

    for u in users:
      if not u.username in column.scores:
        grade = GBGrade()
        grade.scores['score'] = 0
        grade.save()
        column.scores[u.username] = grade

    column.save()

    return render_template("common/auxillaryGrades.html", course = course, col=column, users=users, instructor=instr)
  except (Course.DoesNotExist, GBColumn.DoesNotExist):
    abort(404)
