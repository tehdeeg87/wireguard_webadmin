from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added
from .models import UserACL

@receiver(social_account_added)
def create_acl_on_social_connect(request, sociallogin, **kwargs):
    """
    When a user opts in and links a Google account, create their ACL.
    """
    user = sociallogin.user
    UserACL.objects.get_or_create(user=user)