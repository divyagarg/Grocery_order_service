# Newapp

## How to run
1. Checkout
2. Install required packages :
pip install -r requirements.txt
3. set ENV VAR "LOG_HOME"
export LOG_HOME="/tmp/logs"
4. run
python manage.py runserver

## Todo:
1. Search for newapp in the project and change it to the project name.
2. Add respective env variables in the staging and production server. We take "development" as HOST_ENV by default.
For
Staging -> Environment variable HOST_ENV = "staging"
Production -> Environment variable HOST_ENV = "production"
3. Also set "LOG_HOME" environment variable to appropriate location. Otherwise it will take "/var/log/<app_name>" as the base log folder.
