# coding=utf-8

#import the app
from app import app

from flask import g, request, render_template, redirect, url_for, flash, abort, jsonify
from flask.ext.login import current_user, login_required

from app.models.course import *
from app.models.pages import *

from app.forms import ProblemOptionsForm, AddTestForm

from werkzeug import secure_filename
import markdown, re


WIKI_LINK_REGEX = r"(?<!!)\[(.+)\]<(.+)>(?:\{:(.+)\})?"
IMG_LINK_REGEX = r"!\[(.+)\]<(.+)>(?:\{:(.+)\})?"
ID_REGEX = r"(?<!\\),"

def extractPageInfo(idents):
  idents = map(lambda x: x.strip(), idents)
  return [None]*(3-len(idents))+idents

def extractImageInfo(idents):
  idents = map(lambda x: x.strip(), idents)
  return [None]*(4-len(idents))+idents

def wikiAdaptations(page):
  linkRegex = re.compile(WIKI_LINK_REGEX)
  imgRegex = re.compile(IMG_LINK_REGEX)
  pageText = page.text

  for link in linkRegex.finditer(pageText):
    try:
      text = link.group(1)
      identifier = link.group(2)
      style = link.group(3)
      if style == None:
        style = ""
      flash(identifier)
      flash(style)

      idents = extractPageInfo(re.split(ID_REGEX, identifier))

      if idents[0] == None:
        idents[0] = page.course.semester

      if idents[1] == None:
        idents[1] = page.course.name


      c = Course.objects.get(semester__startswith=idents[0], name__startswith=idents[1])
      p = Page.objects.get(course=c, title__startswith=idents[2])
      replacement = "<a href='"+url_for('viewPage', pgid=p.id)+"' "+style+">" + text + "</a>"
    except Course.DoesNotExist:
      replacement = "<span style='color:red'>"+text+"[Link failed]</span>"
    except Page.DoesNotExist:
      if idents[2] == "COURSE_PROBLEMS":
        flash("Problem page")
        replacement = "<a href='"+url_for('studentAssignments', cid=c.id)+"'>"+text+"</a>"
      else:
        replacement = "<a href='"+url_for('index')+"' style='color:grey'>" + text + "[?]</a>"


    pageText = re.sub(re.escape(link.group(0)), replacement, pageText, count=1)

  for img in imgRegex.finditer(pageText):
    try:
      text = link.group(1)
      identifier = link.group(2)

      idents = extractPageInfo(re.split(ID_REGEX, identifier))

      if idents[0] == None:
        idents[0] = page.course.semester

      if idents[1] == None:
        idents[1] = page.course.name

      if idents[2] == None:
        idents[2] = page.title


      c = Course.objects.get(semester__startswith=idents[0], name__startswith=idents[1])
      p = Page.objects.get(course=c, title__startswith=idents[2])
      replacement = "<a href='"+url_for('viewPage', pgid=p.id)+"'>" + text + "</a>"
    except Course.DoesNotExist:
      replacement = "<span style='color:red'>[Image failed to load. Course not found]</span>"
    except Page.DoesNotExist:
      replacement = "<span style='color:red'>[Image failed to load. Page not found]</span>"


    pageText = re.sub(re.escape(link.group(0)), replacement, pageText, count=1)

  return pageText


@app.route('/page/view/id/<pgid>')
def viewPage(pgid):
  page = Page.objects.get(id=pgid)
  text = wikiAdaptations(page)
  if page.canView(g.user):
    return render_template('pages/viewpage.html', page=page, text=text)
  else:
    abort(403)


@app.route('/page/edit/id/<pgid>')
@login_required
def editPage(pgid):
  page = Page.objects.get(id=pgid)
  text = wikiAdaptations(page)
  if page.canEdit(g.user):
    return render_template('pages/editpage.html', page=page, text=text)
  else:
    abort(403)

@app.route('/page/save/<pgid>', methods=['POST'])
@login_required
def savePage(pgid):
  try:
    page = Page.objects.get(id=pgid)
    if not page.canEdit(g.user):
      abort(403)
    content = request.get_json()
    page.text = content['text']
    page.title = content['title']
    page.perm['anyView'] = content['perm']['anyView']
    page.perm['userView'] = content['perm']['userView']
    page.perm['cUserView'] = content['perm']['cUserView']
    page.perm['grutorView'] = content['perm']['grutorView']
    page.perm['cGrutorView'] = content['perm']['cGrutorView']
    page.perm['userEdit'] = content['perm']['userEdit']
    page.perm['cUserEdit'] = content['perm']['cUserEdit']
    page.perm['grutorEdit'] = content['perm']['grutorEdit']
    page.perm['cGrutorEdit'] = content['perm']['cGrutorEdit']
    page.save()
    return jsonify(res=True)
  except Exception as e:
    return jsonify(res=str(e))

@app.route('/page/preview/<pgid>', methods=['POST'])
@login_required
def pagePreview(pgid):
  '''
  Funcion Type: Callback-AJAX Function
  Called By: grutor/gradesubmission.html:$("#previewBtn").click(...)
  Purpose: Produce HTML from a given markdown string.

  Inputs:
    pgid: The page that this preview is of. This is used for dealing with links

  POST Values: A json object containing one field called "text" which contains
  the markdown formatted string.

  Outputs:
    res: The resulting html generated from the markdown
  '''
  content = request.get_json()
  try:
    pg = Page.objects.get(id=pgid)
    pg.text = content["text"]
    html = markdown.markdown(wikiAdaptations(pg))
    return jsonify(res=html)
  except Exception as e:
    return jsonify(res=str(e))

@app.route('/page/make/<cid>/<title>')
@login_required
def pageMake(cid, title):
  pass
