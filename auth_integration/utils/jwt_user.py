from django.contrib.auth.models import User
from user_manager.models import UserAcl
from wireguard.models import PeerGroup, WireGuardInstance


def ensure_user_from_jwt(claims):
    """
    Ensure a Django User + UserAcl exists for the JWT subject.
    """
    username = claims.get("username") or claims.get("sub", "unknown_user")
    email = claims.get("email") or f"{username}@portbro.com"  # Handle null email
    role = claims.get("role", "basic")
    userlevel = claims.get("userlevel")  # Direct userlevel from portbro.com

    # Ensure email is not empty or None
    if not email or email.strip() == "":
        email = f"{username}@portbro.com"

    user, created = User.objects.get_or_create(username=username, defaults={"email": email})
    
    # Update email if it's different (for existing users)
    if not created and user.email != email:
        user.email = email
        user.save()

    acl, _ = UserAcl.objects.get_or_create(user=user)

    # Map userlevel or role → user_level
    if userlevel is not None:
        # Use direct userlevel from portbro.com
        acl.user_level = userlevel
    elif role == "admin":
        acl.user_level = 50
    elif role == "manager":
        acl.user_level = 40
    else:
        acl.user_level = 30  # peer manager by default

    acl.enable_reload = True
    acl.enable_restart = True
    acl.enable_console = True
    acl.save()

    # SECURITY FIX: Don't automatically assign users to instances
    # Users should only be assigned to instances they're supposed to have access to
    # This prevents users from seeing instances they shouldn't have access to
    
    # Check if user already has a peer group assigned
    if not acl.peer_groups.exists():
        # Only create a peer group if user doesn't have one already
        group, created = PeerGroup.objects.get_or_create(name=f"{username}_group")
        acl.peer_groups.add(group)
    
    # Note: Instance assignment should be done manually by administrators
    # or through proper business logic, not automatically on every login

    return user
