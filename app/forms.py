from flask.ext.wtf import Form
from wtforms import TextField, PasswordField, validators, HiddenField, BooleanField, SelectField
from wtforms import TextAreaField, BooleanField, FileField
from wtforms.validators import Required, EqualTo, Optional
from wtforms.validators import Length, Email

'''
Account management forms
'''

class SignInForm(Form):
	username = TextField('Username',validators=[Required('Please provide a username')])
	password = PasswordField('Password', validators=[Required()])
	remember = BooleanField('Remember Me')

class ChangePasswordForm(Form):
	oldPassword = PasswordField('Old Password', validators=[Required()])
	newPassword = PasswordField('New Password', validators=[Required()])
	newPasswordConf = PasswordField('Confirm New Password', validators=[Required()])

class ChangeFirstNameForm(Form):
	firstName = TextField('First Name')

class ChangeLastNameForm(Form):
	lastName = TextField('Last Name')

class ChangeEmailForm(Form):
	email = TextField('Email', validators=[Email()])


'''
Admin panel forms
'''

class CreateCourseForm(Form):
	name = TextField("Course Name")
	semester = TextField("Semester")

class CreateUserForm(Form):
	firstName = TextField("First Name")
	lastName = TextField("Last Name")
	username = TextField("Username")
	email = TextField("Email")
	password = PasswordField("Password")


'''
Instructor forms
'''

class CreateAssignmentForm(Form):
	name = TextField("Assignment Group Name", validators=[Required()])

class AddUserCourseForm(Form):
	uname = TextField("Username", validators=[Required()])

class ProblemOptionsForm(Form):
	name = TextField("Problem Name")
	date = TextField("Due Date")
	time = TextField("Due Time")
	hiddentime = TextField("")

class AddTestForm(Form):
	testFile = FileField("File")
	testType = SelectField("Language", choices=[('python', 'Python')])


'''
Student forms
'''

class SubmitAssignmentForm(Form):
	files = FileField("Files")
