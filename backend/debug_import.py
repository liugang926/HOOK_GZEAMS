import os
import django
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

print("1. Importing Asset Model...")
from apps.assets.models import Asset
print("2. Importing AssetOperationService...")
from apps.assets.services.operation_service import AssetPickupService
print("3. Done.")
