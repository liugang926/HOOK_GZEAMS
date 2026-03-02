import os
import django
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

print("1. Importing Consumables Model...")
from apps.consumables.models import Consumable
print("2. Done.")
