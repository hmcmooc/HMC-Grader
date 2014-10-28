# -*- coding: utf-8 -*-

'''
This module handles login, logout, and settings for user accounts
'''

#import the app and the login manager
from app import app, loginManager

from flask import g, request, render_template, redirect, url_for
from flask.ext.login import login_user, logout_user, current_user, login_required

from flask.ext.mongoengine import DoesNotExist

from models import User
from forms import SignInForm, ChangePasswordForm, ChangeFirstNameForm\
                  ,ChangeLastNameForm, ChangeEmailForm

LOGIN_ERROR_MSG = "Invalid Username/Password"


@loginManager.user_loader
def load_user(id):
  '''
  Function Type: Boilerplate
  Purpose: This function takes the user ID stored in the session cookie and
  converts it into a User object by performing a database query.
  '''
  return User.objects.get(id=id)

@app.route('/login', methods=['POST', 'GET'])
def login():
  '''
  Function Type: View Function, Form handler
  Template: accounts/login.html
  Purpose: Handle the login of a user and provide feedback when login fails.

  Inputs: None

  Template Parameters:
    form: A form of the class SignInForm. This takes the username and password
    of the user.
    active_pate: A string naming the active page. This is for higlighting the
    active page in the nav-bar.

  Forms Handled:
    SignInForm: Uses this form to determine if the user has the credentials to
    access the account. If an error occurs the appropriate error fields are
    filled in and the form is sent back to the template.
  '''
  #If the user is already authenticated we are done here just go to the index
  if g.user is not None and g.user.is_authenticated():
    return redirect(url_for('index'))

  #If the form is being submitted (we get a POST request) handle the login
  if request.method == 'POST':
    form = SignInForm(request.form)
    if form.validate():
      try:
        user = User.objects.get(username=form.username.data)
        passMatch = user.checkPassword(form.password.data)
        #Check for matching password hashes
        if not passMatch:
          form.password.errors.append(LOGIN_ERROR_MSG)
          return render_template("accounts/login.html", form=form, \
                                  active_page="login")

        #Validated so login the user (If the asked to be remembered tell
        #flask-login to handle that)
        login_user(user, remember=form.remember.data)
        #set the session global user variable
        g.user = current_user
        return redirect(url_for('index'))

      except User.DoesNotExist:
        form.password.errors.append(LOGIN_ERROR_MSG)
        return render_template("accounts/login.html", form=form, \
                                active_page="login")

  #If it wasn't a form submission just render a blank form
  return render_template("accounts/login.html", form=SignInForm(), \
                          active_page="login")

@app.route('/logout')
@login_required
def logout():
  '''
  Function Type: Callback-Redirect Function
  Purpose: Log out the current user and redirect to the index

  Inputs: None

  Forms Handled: None
  '''
  logout_user()
  g.user = current_user
  return redirect(url_for('index'))

#TODO refactor this. possibly use javascript and a smaller callback rather than this large elif mess
@app.route('/settings', methods=['POST', 'GET'])
@login_required
def userSettings():
  '''
  Function Type: View Function
  Template: accounts/settings.html
  Purpose: Display current account information as well as provide forms for
  changing account information.

  Inputs: None

  Template Parameters:
    pwform: PasswordChangeForm for allowing the user to change their password
    fnform: Form for changing first names
    lnform: Form for changing last names
    eform: Form for changing email addresses
    active_page: Identifier for highlighting the active page in the nav-bar

  Forms Handled:
    PasswordChangeForm: Confirms that the old password matches and that the two
    new passwords match then changes the users password.
    ChangeFirstNameForm: Changes the users first name
    ChangeLastNameForm: Changes the users last name
    ChangeEmailForm: Changes the users email
  '''
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
