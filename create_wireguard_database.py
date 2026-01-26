#!/usr/bin/env python3
"""
Script to create a new PostgreSQL database for WireGuard cluster.
This will create a new database in your existing PostgreSQL instance.
"""
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database connection details
DB_HOST = os.getenv('DB_HOST', 'app-56298fa7-c784-4d2d-96ea-1487a44fece1-do-user-14643983-0.k.db.ondigitalocean.com')
DB_PORT = os.getenv('DB_PORT', '25060')
DB_USER = os.getenv('DB_USER', 'dbpo')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME_NEW = os.getenv('DB_NAME_NEW', 'wireguard_cluster')
DB_USER_NEW = os.getenv('DB_USER_NEW', 'wireguard_user')  # Optional: new user for wireguard database

# If password not in env, prompt for it
if not DB_PASSWORD:
    import getpass
    DB_PASSWORD = getpass.getpass(f'Enter password for PostgreSQL user {DB_USER}: ')

def create_database():
    """Create the wireguard_cluster database."""
    try:
        # Connect to PostgreSQL server (connect to default 'postgres' database to create new one)
        print(f"Connecting to PostgreSQL server at {DB_HOST}:{DB_PORT}...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database='postgres',  # Connect to default database to create new one
            sslmode='require'
        )
        
        # Set isolation level to allow database creation
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database already exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (DB_NAME_NEW,)
        )
        exists = cursor.fetchone()
        
        if exists:
            print(f"Database '{DB_NAME_NEW}' already exists.")
            response = input("Do you want to drop and recreate it? (yes/no): ").strip().lower()
            if response == 'yes':
                print(f"Dropping existing database '{DB_NAME_NEW}'...")
                cursor.execute(f'DROP DATABASE "{DB_NAME_NEW}"')
                print("Database dropped.")
            else:
                print("Skipping database creation.")
                return True
        
        # Create the new database
        print(f"Creating database '{DB_NAME_NEW}'...")
        cursor.execute(f'CREATE DATABASE "{DB_NAME_NEW}"')
        print(f"✓ Database '{DB_NAME_NEW}' created successfully!")
        
        # Optionally create a dedicated user for the wireguard database
        create_user = input(f"\nDo you want to create a dedicated user '{DB_USER_NEW}' for this database? (yes/no): ").strip().lower()
        if create_user == 'yes':
            user_password = getpass.getpass(f'Enter password for new user {DB_USER_NEW}: ')
            user_password_confirm = getpass.getpass('Confirm password: ')
            
            if user_password != user_password_confirm:
                print("Passwords do not match. Skipping user creation.")
            else:
                try:
                    # Create user
                    cursor.execute(f"CREATE USER {DB_USER_NEW} WITH PASSWORD %s", (user_password,))
                    print(f"✓ User '{DB_USER_NEW}' created successfully!")
                    
                    # Grant privileges
                    cursor.execute(f'GRANT ALL PRIVILEGES ON DATABASE "{DB_NAME_NEW}" TO {DB_USER_NEW}')
                    print(f"✓ Granted all privileges on '{DB_NAME_NEW}' to '{DB_USER_NEW}'")
                    
                    # Connect to the new database to grant schema privileges
                    conn.close()
                    conn = psycopg2.connect(
                        host=DB_HOST,
                        port=DB_PORT,
                        user=DB_USER,
                        password=DB_PASSWORD,
                        database=DB_NAME_NEW,
                        sslmode='require'
                    )
                    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                    cursor = conn.cursor()
                    
                    # Grant schema privileges
                    cursor.execute(f'GRANT ALL ON SCHEMA public TO {DB_USER_NEW}')
                    print(f"✓ Granted schema privileges to '{DB_USER_NEW}'")
                    
                except psycopg2.Error as e:
                    print(f"Warning: Could not create user (may already exist): {e}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("Database setup complete!")
        print("="*60)
        print(f"\nDatabase Name: {DB_NAME_NEW}")
        print(f"Host: {DB_HOST}")
        print(f"Port: {DB_PORT}")
        if create_user == 'yes':
            print(f"User: {DB_USER_NEW}")
        else:
            print(f"User: {DB_USER} (using existing user)")
        print("\nYou can now update your Django settings.py to use this database.")
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"Error connecting to database: {e}")
        print("\nPlease check:")
        print("  - Database host and port are correct")
        print("  - Username and password are correct")
        print("  - Your IP is whitelisted in DigitalOcean (if required)")
        print("  - SSL connection is allowed")
        return False
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == '__main__':
    print("="*60)
    print("WireGuard Cluster Database Setup")
    print("="*60)
    print()
    
    success = create_database()
    sys.exit(0 if success else 1)
