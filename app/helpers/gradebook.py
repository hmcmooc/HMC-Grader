# coding=utf-8

from app.plugins.latework import getLateCalculators

def getStudentAssignmentScores(course, user):
  '''Generates a gradelist and runs it through the late calculator'''
  # Create a gradelist
  gl = []
  for a in course.assignments:
    al = []
    for p in sorted(a.problems, key=lambda x: x.name):
      sub = p.getLatestSubmission(user)
      if not sub == None:
        gradeData = {}
        gradeData['rawTotalScore'] = sub.grade.totalScore()
        gradeData['timeDelta'] = p.duedate - sub.submissionTime
        gradeData['isLate'] = sub.isLate
        gradeData['maxScore'] = p.totalPoints()
        al.append(gradeData)
      else:
        al.append(None)
    gl.append(al)

  lateCalculator = getLateCalculators()[course.lateGradePolicy]

  gl = lateCalculator(gl)
  return gl

def getStudentAuxScores(course, user):
  scores = []
  for group in course.gradeBook.auxillaryGrades:
    for col in group.columns:
      scores.append({'score':col.scores[user.username].totalScore(), 'maxScore':col.maxScore})
  return scores
