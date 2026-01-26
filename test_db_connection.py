#!/usr/bin/env python3
"""
Test database connection and show detailed error messages.
"""
import os
import sys

# Check if psycopg2 is available first
try:
    import psycopg2
    from psycopg2 import OperationalError
except ImportError as e:
    print("="*60)
    print("CRITICAL ERROR: psycopg2 is not installed")
    print("="*60)
    print(f"Import error: {e}")
    print()
    print("This means psycopg2-binary is not installed in the container.")
    print("Please check:")
    print("  1. requirements.txt includes 'psycopg2-binary>=2.9.0'")
    print("  2. Docker image was rebuilt: docker-compose build")
    print("  3. libpq5 is installed in the runtime image")
    print()
    sys.exit(1)

import django

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wireguard_webadmin.settings')
django.setup()

from django.db import connection
from django.conf import settings

# Use print for output as logging might not be configured yet
def print_status(message, is_success=True):
    if is_success:
        print(f"\033[92m[SUCCESS]\033[0m {message}") # Green
    else:
        print(f"\033[91m[ERROR]\033[0m {message}") # Red

def print_warning(message):
    print(f"\033[93m[WARNING]\033[0m {message}") # Yellow

print("="*60)
print("Database Connection Test")
print("="*60)
print()

# Show configuration (hide password)
db_config = settings.DATABASES['default']
print(f"Database Engine: {db_config['ENGINE']}")
print(f"Database Name: {db_config['NAME']}")
print(f"Database User: {db_config['USER']}")
print(f"Database Host: {db_config['HOST']}")
print(f"Database Port: {db_config['PORT']}")
print(f"SSL Mode: {db_config.get('OPTIONS', {}).get('sslmode', 'not set')}")
print()

# Try to connect
print("Attempting to connect to database...")
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print_status(f"Connection successful!")
        print(f"PostgreSQL version: {version}")
        
        # Check if tables exist
        cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public');")
        if cursor.fetchone()[0]:
            print_status("Tables found in database (migrations likely run)")
        else:
            print_warning("No tables found in database (migrations not run yet)")
        
        cursor.execute(f"SELECT current_database();")
        current_db = cursor.fetchone()[0]
        print(f"\nConnected to database: {current_db}")
        sys.exit(0) # Exit successfully
except OperationalError as e:
    print_status(f"Connection failed: {e}", is_success=False)
    print("\nPlease check:")
    print("  - Database host and port are correct")
    print("  - Username and password are correct")
    print("  - Your server's IP is whitelisted in DigitalOcean (if required)")
    print("  - Network connectivity from the container to the database host")
    print("  - SSL connection is allowed and configured correctly")
    sys.exit(1) # Exit with error
except Exception as e:
    print_status(f"An unexpected error occurred: {e}", is_success=False)
    sys.exit(1) # Exit with error
