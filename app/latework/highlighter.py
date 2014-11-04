from decimal import Decimal

PLUGIN_NAME = "Highlighter"

def calculateGrades(gradeList):
  '''
  Basic (and default) late calculator only colors late submissions red
  so that they can be noticed in the gradebook
  '''
  for assignment in gradeList:
    for problem in assignment:
      #check for no submission and skip
      if problem is None:
        continue
      if problem['isLate']:
        problem['highlight'] = "red"
        problem['finalTotalScore'] = Decimal('0.00') #This is so it renders the same
  return gradeList
