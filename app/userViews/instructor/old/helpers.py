# coding=utf-8

from datetime import *
from app.models.stats import *

def submissionData(course, start=datetime.min, end=datetime.max):
  buckets = {}
  for d in range(7):
    for h in range(24):
      buckets[(d,h)] = 0
  for a in course.assignments:
    for p in a.problems:
      for sl in p.studentSubmissions.values():
        for s in sl.submissions:
          if s.submissionTime > start and s.submissionTime < end:
            key = (s.submissionTime.weekday(), s.submissionTime.hour)
            buckets[key] += 1

  outList = []
  for k, v in buckets.iteritems():
    outList.append([k[0], k[1], v])
  return outList


def attendanceData(course, start=datetime.min, end=datetime.max):
  stats = StudentStats.objects.filter(course=course, clockIn__gte=start, clockIn__lte=end)
  buckets = {}
  for d in range(7):
    for h in range(24):
      buckets[(d,h)] = 0
  for s in stats:
    key = (s.clockIn.weekday(), s.clockIn.hour)
    buckets[key] += 1

  outList = []
  for k, v in buckets.iteritems():
    outList.append([k[0], k[1], v])
  return outList
