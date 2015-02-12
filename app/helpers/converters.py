# coding=utf-8

from werkzeug.routing import BaseConverter

class BoolConverter(BaseConverter):

  def to_python(self, value):
    return value == "t"

  def to_url(self, value):
    if value == True:
      return "t"
    else:
      return "f"

class TimeConverter(BaseConverter):

  def to_python(self, value):
    import dateutil.parser
    return dateutil.parser.parse(value)

  def to_url(self, value):
    return str(value.isoformat())

class ProblemConverter(BaseConverter):

  def to_python(self, value):
    from app.structures.models.course import Problem
    try:
      return Problem.objects.get(id=value)
    except Problem.DoesNotExist:
      abort(404)

  def to_url(self, value):
    return str(value.id)
