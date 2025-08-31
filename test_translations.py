#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockchart_project.settings')

# Setup Django
django.setup()

from django.utils import translation
from django.utils.translation import gettext as _

def test_translations():
    print("Testing Django internationalization...")
    print(f"Current language: {translation.get_language()}")
    print(f"Available languages: {settings.LANGUAGES}")
    print(f"Locale paths: {settings.LOCALE_PATHS}")
    
    # Test English (default)
    translation.activate('en')
    print(f"\nEnglish translations:")
    print(f"  Home: {_('Home')}")
    print(f"  Predict Stock Prices with AI: {_('Predict Stock Prices with AI')}")
    print(f"  Get Started Free: {_('Get Started Free')}")
    
    # Test Korean
    translation.activate('ko')
    print(f"\nKorean translations:")
    print(f"  Home: {_('Home')}")
    print(f"  Predict Stock Prices with AI: {_('Predict Stock Prices with AI')}")
    print(f"  Get Started Free: {_('Get Started Free')}")
    
    # Check if MO file exists
    mo_file_path = os.path.join(project_dir, 'locale', 'ko', 'LC_MESSAGES', 'django.mo')
    print(f"\nMO file exists: {os.path.exists(mo_file_path)}")
    if os.path.exists(mo_file_path):
        print(f"MO file size: {os.path.getsize(mo_file_path)} bytes")
    
    # Reset to default
    translation.deactivate()

if __name__ == '__main__':
    test_translations()
