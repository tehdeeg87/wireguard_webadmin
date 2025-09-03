from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Called after a successful Google login, before the account is linked.
        Prevent a user from linking multiple social accounts.
        """
        if request.user.is_authenticated:
            # Check if the user already has a linked social account
            if request.user.socialaccount_set.exists():
                # Block the connection
                raise ImmediateHttpResponse(HttpResponse(
                    "You already have a linked SSO account.", status=400
                ))
            # Otherwise, allow linking the first one
            sociallogin.connect(request, request.user)