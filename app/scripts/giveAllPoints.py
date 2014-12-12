# coding=utf-8
import sys
from app.models.course import *
from app.models.user import *

admin = User.objects.get(username="admin")

p = Problem.objects.filter(name="hw11pr1.zip")

print p

if len(p) > 1:
  print "Too many with that name"
  sys.exit(1)

p = p[0]

for u in p.studentSubmissions:
  s = p.studentSubmissions[u].submissions[-1]
  s.grade.scores['Points'] = 30
  s.grade.save()
  s.status = 4
  s.gradedBy = admin
  s.comments = "You got full points for lab."
  s.save()
