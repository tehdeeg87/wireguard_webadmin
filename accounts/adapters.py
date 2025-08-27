from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Called after a successful Google login, before the account is linked.
        If the user is already logged in, connect the social account.
        """
        if request.user.is_authenticated:
            # Link the Google account to the existing user
            sociallogin.connect(request, request.user)