# coding=utf-8

#import the app
from app import app

from app import markdown as app_md

from flask import g, request, render_template, redirect, url_for, flash, abort, jsonify
from flask import send_file
from flask.ext.login import current_user, login_required

from app.models.course import *
from app.models.pages import *

from app.forms import PageImageForm

from werkzeug import secure_filename
from helpers.filestorage import getPagePhotoPath, getPagePhotoDir, ensurePathExists
import re, markdown

from app.helpers.wikiextension import WikiExtension
from markdown.extensions.attr_list import AttrListExtension

@app.route('/page/view/id/<pgid>')
def viewPage(pgid):
  page = Page.objects.get(id=pgid)
  text = markdown.markdown(page.text, [WikiExtension(page), AttrListExtension()])
  if page.canView(g.user):
    return render_template('pages/viewpage.html', page=page, text=text)
  else:
    abort(403)


@app.route('/page/edit/id/<pgid>')
@login_required
def editPage(pgid):
  page = Page.objects.get(id=pgid)
  text = markdown.markdown(page.text, [WikiExtension(page), AttrListExtension()])
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
    html = markdown.markdown(pg.text, [WikiExtension(pg), AttrListExtension()])
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
def servePageImage(pgid, name):
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
