# -*- coding: utf-8 -*-

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for
from flask.ext.login import login_user, logout_user, current_user, login_required

from flask.ext.mongoengine import DoesNotExist

from models import User
from forms import SignInForm, ChangePasswordForm, ChangeFirstNameForm\
                  ,ChangeLastNameForm, ChangeEmailForm

LOGIN_ERROR_MSG = "Invalid Username/Password"

'''
User loader for the login manager. Flask-Login will store the id of the
current user. This function must return the object for that user.
'''
@loginManager.user_loader
def load_user(id):
  return User.objects.get(id=id)

'''
login view function.
Renders the accounts/login.html template.
Validates login information from the SignInForm and redirects to the index if
login is succesful. Otherwise it fill in error fields and re-renders the login
template.
'''
@app.route('/login', methods=['POST', 'GET'])
def login():
  if g.user is not None and g.user.is_authenticated():
    return redirect(url_for('index'))

  if request.method == 'POST':
    form = SignInForm(request.form)
    if form.validate():
      try:
        user = User.objects.get(username=form.username.data)
        passMatch = user.checkPassword(form.password.data)
        #Check for matching password hashes
        if not passMatch:
          form.password.errors.append(LOGIN_ERROR_MSG)
          return render_template("accounts/login.html", form=form, active_page="login")

        #Validated so login the user
        login_user(user, remember=form.remember.data)
        #set the session global user variable
        g.user = current_user
        return redirect(url_for('index'))

      except User.DoesNotExist:
        form.password.errors.append(LOGIN_ERROR_MSG)
        return render_template("accounts/login.html", form=form, active_page="login")

  #If it wasn't a form submission just render a blank form
  return render_template("accounts/login.html", form=SignInForm(), active_page="login")

'''
logout view function.
Doesn't render any template but instead logs out the user and redirects to the
index.
'''
@app.route('/logout')
@login_required
def logout():
  logout_user()
  g.user = current_user
  return redirect(url_for('index'))

'''
Account settings view function.
Renders the accounts/settings.html template.
Also handles the submission of several forms for changing settings of the user.
'''
#TODO refactor this. possibly use javascript and a smaller callback rather than this large elif mess
@app.route('/settings', methods=['POST', 'GET'])
@login_required
def userSettings():
  if request.method == 'POST':
    #Find which form was submitted
    if request.form['btn'] == 'changepasswd':
      form = ChangePasswordForm(request.form)
      if form.validate():
        user = current_user
        pass_match = user.checkPassword(form.oldPassword.data)
        if not pass_match:
          form.oldPassword.errors.append("Please confirm your old password")
          return render_template("accounts/settings.html", pwform=form,\
                                  fnform=ChangeFirstNameForm(), lnform=ChangeLastNameForm(),\
                                  eform=ChangeEmailForm(), active_page="userSettings")
        elif form.newPassword.data != form.newPasswordConf.data:
          form.newPasswordConf.errors.append("Passwords must match")
          return render_template("accounts/settings.html", pwform=form,\
                                  fnform=ChangeFirstNameForm(), lnform=ChangeLastNameForm(),\
                                  eform=ChangeEmailForm(), active_page="userSettings")
        else:
          user.setPassword(form.newPassword.data)
          user.save()
          return redirect(url_for('userSettings'))
    elif request.form['btn'] == 'changefn':
      form = ChangeFirstNameForm()
      if form.validate():
        user = current_user
        user.firstName = form.firstName.data
        user.save()
        return redirect(url_for('userSettings'))
    elif request.form['btn'] == 'changeln':
      form = ChangeLastNameForm()
      if form.validate():
        user = current_user
        user.lastName = form.lastName.data
        user.save()
        return redirect(url_for('userSettings'))
    elif request.form['btn'] == 'changeemail':
      form = ChangeEmailForm()
      if form.validate():
        user = current_user
        user.email = form.email.data
        user.save()
        return redirect(url_for('userSettings'))
  return render_template("accounts/settings.html", pwform=ChangePasswordForm(),\
                          fnform=ChangeFirstNameForm(), lnform=ChangeLastNameForm(),\
                          eform=ChangeEmailForm(), active_page="userSettings")
