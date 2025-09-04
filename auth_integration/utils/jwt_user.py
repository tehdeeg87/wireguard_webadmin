from django.contrib.auth.models import User
from wireguard.models import UserAcl, PeerGroup, WireGuardInstance


def ensure_user_from_jwt(claims):
    """
    Ensure a Django User + UserAcl exists for the JWT subject.
    """
    username = claims["sub"]  # unique user ID from portbro.com
    email = claims.get("email", f"{username}@portbro.com")
    role = claims.get("role", "basic")

    user, _ = User.objects.get_or_create(username=username, defaults={"email": email})

    acl, _ = UserAcl.objects.get_or_create(user=user)

    # Map role → user_level
    if role == "admin":
        acl.userlevel = 50
    elif role == "manager":
        acl.userlevel = 40
    else:
        acl.userlevel = 30  # peer manager by default

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
        pass  # skip if no instance yet

    return user
