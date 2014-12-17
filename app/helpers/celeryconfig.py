from celery import Celery

'''
Make a celery object based on the app configuration.

Celery is a distrubuted asynchronous task system. It is used to allow the autograder
to run on another machine and not block the webpage.
'''
def make_celery(app):
  celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
  celery.conf.update(app.config)
  TaskBase = celery.Task
  class ContextTask(TaskBase):
    abstract = True
    def __call__(self, *args, **kwargs):
      with app.app_context():
        return TaskBase.__call__(self, *args, **kwargs)
  celery.Task = ContextTask
  return celery
