import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wireguard_webadmin.settings')
django.setup()

from django.contrib.auth.models import User
from user_manager.models import UserAcl
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_user_creation():
    try:
        # Test user data
        username = 'testuser'
        email = 'test@example.com'
        password = 'password'

        # Check if user exists
        if User.objects.filter(username=username).exists():
            logger.info(f"User {username} already exists")
            return

        # Create user
        logger.info(f"Attempting to create user: {username}")
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        logger.info(f"User created successfully: {user.username}")

        # Create UserAcl
        logger.info(f"Attempting to create UserAcl for user: {user.username}")
        user_acl = UserAcl.objects.create(
            user=user,
            user_level=20,
            can_reload_wireguard=False,
            can_restart_wireguard=False
        )
        logger.info(f"UserAcl created successfully: {user_acl.uuid}")

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")

if __name__ == '__main__':
    test_user_creation() 