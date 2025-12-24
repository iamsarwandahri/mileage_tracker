import os
import sys

# Add your project directory to the sys.path
project_home = '/home/yourusername/your-project-name'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variable to tell django where the settings are
os.environ['DJANGO_SETTINGS_MODULE'] = 'mileage_tracker.settings_production'

# Set the virtual environment
activate_this = '/home/yourusername/myenv/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

# Import django and start wsgi
import django
django.setup()

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()