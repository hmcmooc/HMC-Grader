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
MONGODB_SETTINGS = {'DB': 'submissionsite'}

DATABASE_QUERY_TIMEOUT = 0.5

#
#Celery config ssettings
#
CELERY_BROKER_URL="amqp://guest@localhost"

#
# Settings for file storage
#
STORAGE_HOME="/home/plenk/GroodyGrader"


#
# Email settings
#

SYSTEM_EMAIL_ADDRESS = "cloud@cs.hmc.edu"

SMTP_SERVER = "knuth.cs.hmc.edu"
