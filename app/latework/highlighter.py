PLUGIN_NAME = "Highlighter"

def calculateGrades(gradeList):
  '''
  Basic (and default) late calculator only colors late submissions red
  so that they can be noticed in the gradebook
  '''
  for assignment in gradeList:
    for problem in assignment:
      if problem['isLate']:
        problem['higlight'] = "red"
  return gradeList
