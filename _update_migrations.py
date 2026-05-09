import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from django.db import connection
cursor = connection.cursor()
cursor.execute("UPDATE django_migrations SET app = 'celebs' WHERE app = 'stars'")
connection.commit()
print('Rows updated:', cursor.rowcount)
