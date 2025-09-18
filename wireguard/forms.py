import ipaddress

from django import forms
from django.utils.translation import gettext_lazy as _

from wgwadmlibrary.tools import is_valid_ip_or_hostname
from .models import NETMASK_CHOICES, WireGuardInstance


class WireGuardInstanceForm(forms.ModelForm):
    name = forms.CharField(label=_('Display Name'), required=False)
    instance_id = forms.IntegerField(label=_('Instance ID'))
    private_key = forms.CharField(label=_('Private Key'))
    public_key = forms.CharField(label=_('Public Key'))
    hostname = forms.CharField(label=_('Public Address'))
    listen_port = forms.IntegerField(label=_('Listen Port'))
    address = forms.GenericIPAddressField(label=_('Internal IP Address'))
    netmask = forms.ChoiceField(choices=NETMASK_CHOICES, label=_('Netmask'))
    post_up = forms.CharField(label=_('Post Up'), required=False)
    post_down = forms.CharField(label=_('Post Down'), required=False)
    peer_list_refresh_interval = forms.IntegerField(label=_('Web Refresh Interval'), initial=10)
    dns_primary = forms.GenericIPAddressField(label=_('Primary DNS'), initial='172.19.0.2', required=False)
    dns_secondary = forms.GenericIPAddressField(label=_('Secondary DNS'), initial='8.8.8.8', required=False)
    bandwidth_limit_enabled = forms.BooleanField(label=_('Enable Bandwidth Limiting'), initial=True, required=False)
    bandwidth_limit_mbps = forms.IntegerField(label=_('Bandwidth Limit (Mbps)'), initial=50, min_value=1, max_value=10000, required=False)

    class Meta:
        model = WireGuardInstance
        fields = [
            'name', 'instance_id', 'private_key', 'public_key','hostname', 'listen_port', 'address', 
            'netmask', 'post_up', 'post_down', 'peer_list_refresh_interval', 'dns_primary', 'dns_secondary',
            'bandwidth_limit_enabled', 'bandwidth_limit_mbps'
            ]
        
    def clean(self):
        cleaned_data = super().clean()
        hostname = cleaned_data.get('hostname')
        address = cleaned_data.get('address')
        netmask = cleaned_data.get('netmask')
        post_up = cleaned_data.get('post_up')
        post_down = cleaned_data.get('post_down')

        peer_list_refresh_interval = cleaned_data.get('peer_list_refresh_interval')
        if peer_list_refresh_interval is not None and peer_list_refresh_interval < 5:
            raise forms.ValidationError(_('Peer List Refresh Interval must be at least 5 seconds'))
        
        bandwidth_limit_mbps = cleaned_data.get('bandwidth_limit_mbps')
        if bandwidth_limit_mbps is not None and (bandwidth_limit_mbps < 1 or bandwidth_limit_mbps > 10000):
            raise forms.ValidationError(_('Bandwidth limit must be between 1 and 10000 Mbps'))

        if hostname and not is_valid_ip_or_hostname(hostname):
            raise forms.ValidationError(_('Invalid hostname or IP Address'))

        if address and netmask:
            try:
                current_network = ipaddress.ip_network(f"{address}/{netmask}", strict=False)
                all_other_instances = WireGuardInstance.objects.all()
                if self.instance:
                    all_other_instances = all_other_instances.exclude(uuid=self.instance.uuid)
                for instance in all_other_instances:
                    other_network = ipaddress.ip_network(f"{instance.address}/{instance.netmask}", strict=False)
                    if current_network.overlaps(other_network):
                        raise forms.ValidationError(_('The selected network range overlaps with another instance.'))
            except (ValueError, TypeError) as e:
                raise forms.ValidationError(_('Invalid network configuration: {}').format(str(e)))

        #if self.instance:
        #    if post_up or post_down:
        #        if self.instance.post_up != post_up or self.instance.post_down != post_down:
        #            raise forms.ValidationError('Post Up and Post Down cannot be changed, please go to Firewall page to make changes to the firewall.')
        #else:
        #    if post_up or post_down:
        #        raise forms.ValidationError('Post Up and Post Down cannot be set, please go to Firewall page to make changes to the firewall.')
            
        return cleaned_data

