import collections
import logging

import django
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import forms as django_auth_forms
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_post_parameters

from openstack_auth import exceptions
from openstack_auth import utils

LOG = logging.getLogger(__name__)

class LoginViaToken(django_auth_forms.AuthenticationForm):
    region = forms.ChoiceField(label = _("Region"), required= False)
    token = forms.CharField(
        label =_("Keystone token"),
        widget = forms.TextInput(attrs = {"autofocus": "autofocus"})
    )
    
    def __init__(self, *args, **kwargs):
        super(LoginViaToken, self).__init__(*args, **kwargs)
        fields_ordering = ['token', 'region']
        if getattr(settings, 'OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT',
                   False):
            self.fields['domain'] = forms.CharField(
                label =_("Domain"),
                required = True,
                widget = forms.TextInput(attrs={"autofocus":"autofocus"})
            )
            self.fields['token'].widget = forms.widget.TextInput()
            fields_ordering = ['domain', 'token', 'region']
        self.fields['region'].choices = self.get_region_choices()
        if len(self.fields['region'].choices) == 1:
            self.fields['region'].initial = self.fields['region'].choices[0][0]
            self.fields['region'].widget = forms.widget.HiddenInput()
        elif len(self.fields['region'].choices) > 1:
            self.fields['region'].initial = self.request.COOKIES.get('login_region')
        if utils.is_websso_enabled():
            initial = getattr(settings, 'WEBSSO_INITIAL_CHOICE', 'credentials')
            self.fields['auth_type'] = forms.ChoiceField(
                label = ("Authenticate using"),
                choices = getattr(settings, 'WEBSSO_CHOICES', ()),
                required = False,
                initial = initial
            )
            fields_ordering.insert(0, 'auth_type')
        elif getattr(settings, 'WEBSSO_ENABLED', False):
            msg = ("Websso is enabled but horizon is not configured to work " + "with keystone version 3 or above.")
            LOG.warning(msg)
        if django.VERSION >= (1,7):
            self.fields = collections.OrderedDict(
                (key, self.fields[key]) for key in fields_ordering
            )
        else:
            self.fields.keyOrder = fields_ordering
    @staticmethod
    def get_region_choices():
        default_region = (settings.OPENSTACK_KEYSTONE_URL, "Default Region")
        regions = getattr(settings, 'AVAILABLE_REGIONS', [])
        if not regions:
            regions = [default_region]
        return regions
    @sensitive_variables()
    def clean(self):
        default_domain = getattr(settings, 'OPENSTACK_KEYSTONE_DEFAULT_DOMAIN', 'Default')
        token = self.cleaned_data.get('token')
        region = self.cleaned_data.get('region')
        domain = self.cleaned_data.get('domain', default_domain)
        
        try:
            self.user_cache = authenticate(request=self.request, token=token, user_domain_name = domain, auth_url = region)
            msg = 'Login successful for token'
            LOG.info(msg)
        except exceptions.KeystoneAuthException as exc:
            msg = 'Login falied for token'
            LOG.warning(msg)
            raise forms.ValidationError(exc)
        if hasattr(self, 'check_for_test_cookie'):
            self.check_for_test_cookie()
        return self.cleaned_data
            
            