# coding=utf-8

'''
This module handles the comments page
'''

#Import the app
from app import app

#Import needed flask functions
from flask import g, render_template, redirect, url_for, flash, jsonify, abort
from flask import request, after_this_request, send_file
from flask.ext.login import current_user, login_required

#Import forms
from app.structures.forms import FeedbackForm

#Import helpers
from app.helpers.filestorage import ensurePathExists, getCommentPath

#import python libraries
import hashlib, datetime, os


@app.route('/comments')
@login_required
def writeComment():
  return render_template('common/feedback.html', form=FeedbackForm())

@app.route('/comment/submit', methods=['POST'])
@login_required
def submitComment():
  if request.method == 'POST':
    form = FeedbackForm(request.form)
    if form.validate():
      ensurePathExists(getCommentPath())
      time = datetime.datetime.utcnow()
      filename = hashlib.md5(current_user.username).hexdigest()\
                  + time.isoformat() + ".txt"
      with open(os.path.join(getCommentPath(), filename), 'w') as f:
        if form.useName.data:
          f.write("User: " + current_user.username + "\n")
        f.write("Time: " + time.isoformat() + "\n")
        f.write("Comment:\n" + form.comment.data + "\n")

      flash("Your comment has been submitted", "success")

  return redirect(url_for('writeComment'))
