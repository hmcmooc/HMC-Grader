# coding=utf-8

import os
basedir = os.path.abspath(os.path.dirname(__file__))

#
# Settings for WTForms
#
CSRF_ENABLES=True
SECRET_KEY="Grutors <3 SPAM"

#
#Mongo settings
#
MONGODB_SETTINGS = {'DB': 'submissionsite',
'username': 'grader',
'password': 'grutorsLoveGrading',
'host': '134.173.43.77'}

DATABASE_QUERY_TIMEOUT = 0.5

#
#Celery config ssettings
#
CELERY_BROKER_URL="amqp://grader:grutorsLoveGrading@134.173.43.77"

#
# Settings for file storage
#
STORAGE_HOME="/home/hmcgrader/GraderStorage"


#
# Email settings
#

SYSTEM_EMAIL_ADDRESS = "cloud@cs.hmc.edu"

SMTP_SERVER = "knuth.cs.hmc.edu"


#
# Autograder settings
#

AUTOGRADER_PLUGIN_PATH = os.path.join(STORAGE_HOME, "plugins/autograder")
LATEWORK_PLUGIN_PATH = os.path.join(STORAGE_HOME, "plugins/latework")

GRADER_USER = None
