# coding=utf-8

#import the app
from app import app, markdown

from flask import g, request, render_template, redirect, url_for, flash, abort, jsonify
from flask import send_file
from flask.ext.login import current_user, login_required

from app.models.course import *
from app.models.pages import *

from app.forms import PageImageForm

from werkzeug import secure_filename
from helpers.filestorage import getPagePhotoPath, getPagePhotoDir, ensurePathExists
import re


WIKI_LINK_REGEX = r"(?<!!)\[(.+)\]<((?:[^<\\>]|\\.)+?)>(?:\{:(.+)\})?"
IMG_LINK_REGEX = r"!\[(.+)\]<((?:[^<\\>]|\\.)+?)>(?:\{:(.+)\})?"
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

      identifier = re.sub(r'\\(.)', r'\1', identifier)
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
        replacement = "<a href='"+url_for('studentAssignments', cid=c.id)+"'>"+text+"</a>"
      else:
        replacement = "<a href='"+url_for('pageMake', pgid=page.id, title=idents[2])+"' style='color:grey'>" + text + "[?]</a>"


    pageText = re.sub(re.escape(link.group(0)), replacement, pageText, count=1)

  for img in imgRegex.finditer(pageText):
    try:
      text = img.group(1)
      identifier = img.group(2)

      idents = extractImageInfo(re.split(ID_REGEX, identifier))

      if idents[0] == None:
        idents[0] = page.course.semester

      if idents[1] == None:
        idents[1] = page.course.name

      if idents[2] == None:
        idents[2] = page.title


      c = Course.objects.get(semester__startswith=idents[0], name__startswith=idents[1])
      p = Page.objects.get(course=c, title__startswith=idents[2])
      replacement = "<img src='"+url_for('serveImage', pgid=p.id, name=idents[3])+"'" + style + ">"
    except Course.DoesNotExist:
      replacement = "<span style='color:red'>[Image failed to load. Course not found]</span>"
    except Page.DoesNotExist:
      replacement = "<span style='color:red'>[Image failed to load. Page not found]</span>"


    pageText = re.sub(re.escape(img.group(0)), replacement, pageText, count=1)

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
    return render_template('pages/editpage.html', page=page, text=text, form=PageImageForm())
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
    html = markdown(wikiAdaptations(pg))
    return jsonify(res=html)
  except Exception as e:
    return jsonify(res=str(e))

@app.route('/page/make/<pgid>/<title>')
@login_required
def pageMake(pgid, title):
  '''
  Function Type: Redirect Function
  Purpose: To make a new page in a course
  '''
  try:
    prevPage = Page.objects.get(id=pgid)
    if not prevPage.canEdit(g.user):
      flash("You aren't allowed to edit this page.")
      return redirect(url_for('viewPage', pgid=pgid))
    page = Page()
    page.title = title
    page.course = prevPage.course
    page.perm = prevPage.perm

    page.save()

    return redirect(url_for('editPage', pgid=page.id))

  except Page.DoesNotExist:
    abort(404)


@app.route('/page/img/<pgid>/<name>')
def serveImage(pgid, name):
  try:
    page = Page.objects.get(id=pgid)
    photoPath = getPagePhotoPath(page, name)
    return send_file(photoPath)
  except Page.DoesNotExist:
    abort(404)

@app.route('/page/img/upload/<pgid>', methods=['POST'])
@login_required
def uploadImage(pgid):
  try:
    page = Page.objects.get(id=pgid)
    if request.method == 'POST':
      form = PageImageForm(request.form)
      if form.validate():
        file = request.files.getlist('photo')[0]
        ensurePathExists(getPagePhotoDir(page))
        photoName = secure_filename(file.filename)
        file.save(os.path.join(getPagePhotoPath(page, photoName)))
        if not photoName in page.images:
          page.images.append(photoName)
          page.save()
    return redirect(url_for('editPage', pgid=pgid))

  except Page.DoesNotExist:
    abort(404)
