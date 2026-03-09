import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "simonstore.settings")
django.setup()

from django.contrib.auth.models import User

username = "admin"
email = "admin@gmail.com"
password = "admin123"

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print("Superuser creado")
else:
    print("El superuser ya existe")
