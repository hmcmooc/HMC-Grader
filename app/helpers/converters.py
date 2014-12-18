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
