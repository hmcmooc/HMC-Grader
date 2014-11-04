from decimal import Decimal

PLUGIN_NAME = "Euros (Optimized Grade)"

def calculateGrades(gradeList):
  '''
  Basic (and default) late calculator only colors late submissions red
  so that they can be noticed in the gradebook
  '''
  lateAssignments = []
  for i, assignment in enumerate(gradeList):
    for j, problem in enumerate(assignment):
      #check for no submission and skip
      if problem is None:
        continue
      if problem['isLate']:
        lateAssignments.append((i,j))

  lateAssignments.sort(reverse=True, key=lambda x: gradeList[x[0]][x[1]]['rawTotalScore'])
  num = 0
  while num < 3 and num < len(lateAssignments):
    pos = lateAssignments[num]
    gradeList[pos[0]][pos[1]]['highlight'] = "yellow"
    num += 1
  while num < len(lateAssignments):
    pos = lateAssignments[num]
    gradeList[pos[0]][pos[1]]['highlight'] = "red"
    gradeList[pos[0]][pos[1]]['finalTotalScore'] = Decimal('0.00')
    num += 1
  return gradeList
