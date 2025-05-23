import os
import re
import subprocess
from io import BytesIO

import qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import Http404, get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from dns.views import export_dns_configuration
from firewall.models import RedirectRule
from firewall.tools import export_user_firewall, generate_firewall_footer, generate_firewall_header, \
    generate_port_forward_firewall, generate_redirect_dns_rules
from user_manager.models import UserAcl
from vpn_invite.models import PeerInvite
from wgwadmlibrary.tools import user_has_access_to_peer
from wireguard.models import Peer, PeerAllowedIP, WireGuardInstance


def clean_command_field(command_field):
    cleaned_field = re.sub(r'[\r\n]+', '; ', command_field)
    cleaned_field = re.sub(r'[\x00-\x1F\x7F]+', '', cleaned_field)
    return cleaned_field


def generate_peer_config(peer_uuid):
    peer = get_object_or_404(Peer, uuid=peer_uuid)
    wg_instance = peer.wireguard_instance

    priority_zero_ip = PeerAllowedIP.objects.filter(config_file='server', peer=peer, priority=0).first()

    if not priority_zero_ip:
        return "No IP with priority zero found for this peer."

    client_address = f"{priority_zero_ip.allowed_ip}/{priority_zero_ip.netmask}"

    allowed_ips = PeerAllowedIP.objects.filter(peer=peer, config_file='client').order_by('priority')
    if allowed_ips:
        allowed_ips_line = ", ".join([f"{ip.allowed_ip}/{ip.netmask}" for ip in allowed_ips])
    else:
        allowed_ips_line = "0.0.0.0/0, ::/0"
    dns_entries = [wg_instance.dns_primary, wg_instance.dns_secondary]
    dns_line = ", ".join(filter(None, dns_entries))

    config_lines = [
        "[Interface]",
        f"PrivateKey = {peer.private_key}" if peer.private_key else "",
        f"Address = {client_address}",
        f"DNS = {dns_line}" if dns_line else "",
        "\n[Peer]",
        f"PublicKey = {wg_instance.public_key}",
        f"Endpoint = {wg_instance.hostname}:{wg_instance.listen_port}",
        f"AllowedIPs = {allowed_ips_line}",
        f"PresharedKey = {peer.pre_shared_key}" if peer.pre_shared_key else "",
        f"PersistentKeepalive = {peer.persistent_keepalive}",
    ]
    return "\n".join(config_lines)


def export_firewall_configuration():
    firewall_content = generate_firewall_header()
    firewall_content += generate_redirect_dns_rules()
    firewall_content += generate_port_forward_firewall()
    firewall_content += export_user_firewall()
    firewall_content += generate_firewall_footer()
    firewall_path = "/etc/wireguard/wg-firewall.sh"
    with open(firewall_path, "w") as firewall_file:
        firewall_file.write(firewall_content)
    subprocess.run(['chmod', '+x', firewall_path], check=True)
    return


@login_required
def export_wireguard_configs(request):
    if not UserAcl.objects.filter(user=request.user).filter(user_level__gte=30).exists():
        return render(request, 'access_denied.html', {'page_title': 'Access Denied'})
    instances = WireGuardInstance.objects.all()
    base_dir = "/etc/wireguard"

    export_firewall_configuration()
    export_dns_configuration()
    
    firewall_inserted = False
    for instance in instances:
        if instance.legacy_firewall:
            post_up_processed = clean_command_field(instance.post_up) if instance.post_up else ""
            post_down_processed = clean_command_field(instance.post_down) if instance.post_down else ""
            
            if post_up_processed:
                post_up_processed += '; '
            if post_down_processed:
                post_down_processed += '; '

            for redirect_rule in RedirectRule.objects.filter(wireguard_instance=instance):
                rule_text_up = ""
                rule_text_down = ""
                rule_destination = redirect_rule.ip_address
                if redirect_rule.peer:
                    peer_allowed_ip_address = PeerAllowedIP.objects.filter(config_file='server', peer=redirect_rule.peer, netmask=32, priority=0).first()
                    if peer_allowed_ip_address:
                        rule_destination = peer_allowed_ip_address.allowed_ip
                if rule_destination:
                    rule_text_up   = f"iptables -t nat -A PREROUTING -p {redirect_rule.protocol} -d wireguard-webadmin --dport {redirect_rule.port} -j DNAT --to-dest {rule_destination}:{redirect_rule.port} ; "
                    rule_text_down = f"iptables -t nat -D PREROUTING -p {redirect_rule.protocol} -d wireguard-webadmin --dport {redirect_rule.port} -j DNAT --to-dest {rule_destination}:{redirect_rule.port} ; "
                    if redirect_rule.add_forward_rule:
                        rule_text_up   += f"iptables -A FORWARD -d {rule_destination} -p {redirect_rule.protocol} --dport {redirect_rule.port} -j ACCEPT ; "
                        rule_text_down += f"iptables -D FORWARD -d {rule_destination} -p {redirect_rule.protocol} --dport {redirect_rule.port} -j ACCEPT ; "
                    if redirect_rule.masquerade_source:
                        rule_text_up   += f"iptables -t nat -A POSTROUTING -d {rule_destination} -p {redirect_rule.protocol} --dport {redirect_rule.port} -j MASQUERADE ; "
                        rule_text_down += f"iptables -t nat -D POSTROUTING -d {rule_destination} -p {redirect_rule.protocol} --dport {redirect_rule.port} -j MASQUERADE ; "
                    post_up_processed += rule_text_up
                    post_down_processed += rule_text_down
                    
            pass
        else:
            post_down_processed = ''
            
            if not firewall_inserted:
                post_up_processed = '/etc/wireguard/wg-firewall.sh'
                firewall_inserted = True
            else:
                post_up_processed = ''
            

        config_lines = [
            "[Interface]",
            f"PrivateKey = {instance.private_key}",
            f"Address = {instance.address}/{instance.netmask}",
            f"ListenPort = {instance.listen_port}",
            f"PostUp = {post_up_processed}",
            f"PostDown = {post_down_processed}",
        ]

        peers = Peer.objects.filter(wireguard_instance=instance)
        for peer in peers:
            peer_lines = [
                "[Peer]",
                f"PublicKey = {peer.public_key}",
                f"PresharedKey = {peer.pre_shared_key}" if peer.pre_shared_key else "",
                f"PersistentKeepalive = {peer.persistent_keepalive}",
            ]
            allowed_ips = PeerAllowedIP.objects.filter(config_file='server', peer=peer).order_by('priority')
            allowed_ips_line = "AllowedIPs = " + ", ".join([f"{ip.allowed_ip}/{ip.netmask}" for ip in allowed_ips])
            peer_lines.append(allowed_ips_line)
            config_lines.extend(peer_lines)
            config_lines.append("")

        config_content = "\n".join(config_lines)
        config_path = os.path.join(base_dir, f"wg{instance.instance_id}.conf")

        os.makedirs(base_dir, exist_ok=True)

        with open(config_path, "w") as config_file:
            config_file.write(config_content)
    if request.GET.get('action') == 'update_and_restart' or request.GET.get('action') == 'update_and_reload':
        messages.success(request, _("Export successful!|WireGuard configuration files have been exported to /etc/wireguard/."))
    else:
        messages.success(request, _("Export successful!|WireGuard configuration files have been exported to /etc/wireguard/. Don't forget to restart the interfaces."))
    if request.GET.get('action') == 'update_and_restart':
        return redirect('/tools/restart_wireguard/?action=dismiss_warning')
    elif request.GET.get('action') == 'update_and_reload':
        return redirect('/tools/restart_wireguard/?action=dismiss_warning&mode=reload')
    return redirect('/status/')


def download_config_or_qrcode(request):
    # This view is used for private and public use. If the user is not authenticated properly, it will return a 404 instead of 403 to avoid leaking any further information.
    if request.GET.get('token') and request.GET.get('password'):
        PeerInvite.objects.filter(invite_expiration__lt=timezone.now()).delete()
        try:
            peer_invite = get_object_or_404(PeerInvite, uuid=request.GET.get('token'), invite_password=request.GET.get('password'))
            peer = peer_invite.peer
        except:
            raise Http404
    else:
        if not request.user.is_authenticated:
            raise Http404

        if not UserAcl.objects.filter(user=request.user).filter(user_level__gte=20).exists():
            return render(request, 'access_denied.html', {'page_title': 'Access Denied'})
        peer = get_object_or_404(Peer, uuid=request.GET.get('uuid'))
        user_acl = get_object_or_404(UserAcl, user=request.user)

        if not user_has_access_to_peer(user_acl, peer):
            raise Http404

    format_type = request.GET.get('format', 'conf')

    config_content = generate_peer_config(peer.uuid)

    if format_type == 'qrcode':
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(config_content)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        response = HttpResponse(content_type="image/png")
        img_io = BytesIO()
        img.save(img_io)
        img_io.seek(0)
        response.write(img_io.getvalue())

    else:
        response = HttpResponse(config_content, content_type="text/plain")
        peer_filename = re.sub(r'[^a-zA-Z0-9]', '_', str(peer))
        response['Content-Disposition'] = f'attachment; filename="peer_{peer_filename}.conf"'

    return response


@login_required
def restart_wireguard_interfaces(request):
    user_acl = UserAcl.objects.filter(user=request.user).filter(user_level__gte=30).first()
    if not user_acl:
        return render(request, 'access_denied.html', {'page_title': 'Access Denied'})
    mode = request.GET.get('mode', 'restart')
    config_dir = "/etc/wireguard"
    interface_count = 0
    error_count = 0
    for filename in os.listdir(config_dir):
        if filename.endswith(".conf"):
            interface_name = filename[:-5]
            if mode == "reload":
                if not user_acl.enable_reload:
                    return render(request, 'access_denied.html', {'page_title': 'Access Denied'})

                config_path = os.path.join(config_dir, filename)
                with open(config_path, 'r') as f:
                    lines = f.readlines()
                filtered_lines = []
                for line in lines:
                    stripped_line = line.strip()
                    if stripped_line.startswith("Address") or stripped_line.startswith("PostUp") or stripped_line.startswith("PostDown"):
                        continue
                    filtered_lines.append(line)

                temp_config_path = f"/tmp/wgreload_{interface_name}.conf"
                with open(temp_config_path, 'w') as f:
                    f.writelines(filtered_lines)

                reload_command = f"wg syncconf {interface_name} {temp_config_path}"
                result = subprocess.run(reload_command, shell=True, capture_output=True, text=True)
                os.remove(temp_config_path)

                if result.returncode != 0:
                    messages.warning(request, _('Error reloading') + f" {interface_name}|{result.stderr}")
                    error_count += 1
                else:
                    interface_count += 1

            else:
                if not user_acl.enable_restart:
                    return render(request, 'access_denied.html', {'page_title': 'Access Denied'})

                stop_command = f"wg-quick down {interface_name}"
                stop_result = subprocess.run(stop_command, shell=True, capture_output=True, text=True)
                if stop_result.returncode != 0:
                    messages.warning(request, _("Error stopping") + f" {interface_name}|{stop_result.stderr}")
                    error_count += 1
                start_command = f"wg-quick up {interface_name}"
                start_result = subprocess.run(start_command, shell=True, capture_output=True, text=True)
                if start_result.returncode != 0:
                    messages.warning(request, _("Error starting") + f" {interface_name}|{start_result.stderr}")
                    error_count += 1
                else:
                    interface_count += 1

    if interface_count > 0 and error_count == 0:
        if mode == 'reload':
            messages.warning(request, _("WARNING|Please note that the interface was reloaded, not restarted. Double-check if the the peers are working as expected. If you find any issues, please report them."))
            messages.success(request, _("WireGuard reloaded|The WireGuard service has been reloaded."))
        else:
            messages.success(request, _("WireGuard restarted|The WireGuard service has been restarted."))

    elif error_count > 0:
        messages.error(request, _("Errors encountered|Error processing one or more interfaces."))

    if interface_count == 0 and error_count == 0:
        messages.info(request, _("No interfaces found|No WireGuard interfaces were found to process."))
    if request.GET.get('action') == 'dismiss_warning':
        for wireguard_instancee in WireGuardInstance.objects.filter(pending_changes=True):
            wireguard_instancee.pending_changes = False
            wireguard_instancee.save()
    return redirect("/status/")

