from app import celery, db

@celery.task()
def gradeSubmission(pid, uid, subnum):
  pass
