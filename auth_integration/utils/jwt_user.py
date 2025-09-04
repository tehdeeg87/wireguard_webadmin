from django.contrib.auth.models import User
from user_manager.models import UserAcl
from wireguard.models import PeerGroup, WireGuardInstance


def ensure_user_from_jwt(claims):
    """
    Ensure a Django User + UserAcl exists for the JWT subject.
    """
    username = claims.get("sub") or claims.get("username", "unknown_user")
    email = claims.get("email") or f"{username}@portbro.com"  # Handle null email
    role = claims.get("role", "basic")
    userlevel = claims.get("userlevel")  # Direct userlevel from portbro.com

    # Ensure email is not empty or None
    if not email or email.strip() == "":
        email = f"{username}@portbro.com"

    user, _ = User.objects.get_or_create(username=username, defaults={"email": email})

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

    # Ensure they have a peer group & link to latest WG instance
    try:
        instance = WireGuardInstance.objects.latest("created")
        group, _ = PeerGroup.objects.get_or_create(name=f"{username}_group")
        group.server_instance.add(instance)
        acl.peer_groups.add(group)
    except WireGuardInstance.DoesNotExist:
        # If no WireGuard instance exists, create a peer group without linking to instance
        group, _ = PeerGroup.objects.get_or_create(name=f"{username}_group")
        acl.peer_groups.add(group)

    return user
