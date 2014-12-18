import markdown, re

from app.structures.models.course import *
from app.structures.models.pages import *

from flask import url_for

ID_REGEX = r"(?<!\\),"
WIKI_LINK_REGEX = r"(?<!!)\[(.+)\]<((?:[^<\\>]|\\.)+?)>"
IMG_LINK_REGEX =  r"!\[(.*)\]<((?:[^<\\>]|\\.)+?)>"

def extractPageInfo(idents):
  idents = map(lambda x: x.strip(), idents)
  return [None]*(3-len(idents))+idents

def extractImageInfo(idents):
  idents = map(lambda x: x.strip(), idents)
  return [None]*(4-len(idents))+idents

class WikiLinkPattern(markdown.inlinepatterns.Pattern):
  def __init__(self, page):
    markdown.inlinepatterns.Pattern.__init__(self, WIKI_LINK_REGEX)
    self.page = page

  def handleMatch(self, m):
    el = markdown.util.etree.Element('a')
    el.text = m.group(2)

    identifier = m.group(3)
    identifier = re.sub(r'\\(.)', r'\1', identifier)
    idents = extractPageInfo(re.split(ID_REGEX, identifier))

    if idents[0] == None:
      idents[0] = self.page.course.semester

    if idents[1] == None:
      idents[1] = self.page.course.name

    try:
      c = Course.objects.get(semester__startswith=idents[0], name__startswith=idents[1])
      p = Page.objects.get(course=c, title__startswith=idents[2])
      el.set("href", url_for('viewPage', pgid=p.id))
    except Course.DoesNotExist:
      el.set("href", "#")
      el.set("style", "color:red;")
      el.text += " [Course Not Found]"
    except Page.DoesNotExist:
      el.set("href", url_for('pageMake', pgid=self.page.id, title=idents[2]))
      el.set("style", "color:grey;")
      el.text += "[?]"
    return el

class WikiImgPattern(markdown.inlinepatterns.Pattern):
  def __init__(self, page):
    markdown.inlinepatterns.Pattern.__init__(self, IMG_LINK_REGEX)
    self.page = page

  def handleMatch(self, m):
    el = markdown.util.etree.Element('img')
    el.set('alt', m.group(2))

    identifier = m.group(3)
    identifier = re.sub(r'\\(.)', r'\1', identifier)
    idents = extractImageInfo(re.split(ID_REGEX, identifier))

    if idents[0] == None:
      idents[0] = self.page.course.semester

    if idents[1] == None:
      idents[1] = self.page.course.name

    if idents[2] == None:
      idents[2] = self.page.title

    try:
      c = Course.objects.get(semester__startswith=idents[0], name__startswith=idents[1])
      p = Page.objects.get(course=c, title__startswith=idents[2])
      el.set("src", url_for('servePageImage', pgid=p.id, name=idents[3]))
    except Course.DoesNotExist:
      el = markdown.util.etree.Element('b')
      el.set("style", "color:red;")
      el.text = "[Image fetch failed: Course Not Found]"
    except Page.DoesNotExist:
      el = markdown.util.etree.Element('b')
      el.set("style", "color:red;")
      el.text = "[Image fetch failed: Page Not Found]"
    return el

class WikiExtension(markdown.Extension):
  def __init__(self, page):
    self.page = page

  def extendMarkdown(self, md, md_globals):
    # Create the del pattern
    wlp = WikiLinkPattern(self.page)
    wip = WikiImgPattern(self.page)
    # Insert del pattern into markdown parser
    md.inlinePatterns.add('wikilink', wlp, '>link')
    md.inlinePatterns.add('wikiimage', wip, '>image_link')

def makeExtension(configs={}):
    return WikiExtension(configs=configs)
