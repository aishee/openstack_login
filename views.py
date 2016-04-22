import django
import logging
import re
from django.contrib import auth
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as django_auth_views
from django.contrib import messages
from django import http as django_http
from django import shortcuts
from django.utils import functional
from django.utils import http
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from keystoneclient.auth import token_endpoint
from keystoneclient import exceptions as keystone_exceptions
import six

from openstack_auth import exceptions
from openstack_auth_token import forms
from openstack_auth_token.forms import LoginViaToken
from openstack_auth import user as auth_user
from openstack_auth import utils

try:
    is_safe_url = http.is_safe_url
except AttributeError:
    is_safe_url = utils.is_safe_url
    
LOG = logging.getLogger(__name__)

@sensitive_post_parameters()
@csrf_protect
@never_cache
def token(request, template_name = None, extra_context=None, **kwargs):
    if request.method == 'POST':
        auth_type = request.POST.get('auth_type', 'credentials')
        if utils.is_websso_enabled() and auth_type != 'credentials':
            auth_url = request.POST.get('region')
            url = utils.get_websso_url(request, auth_url, auth_type)
            return shortcuts.redirect(url)
    if not template_name:
        if request.is_ajax():
            template_name = 'auth/_loginviatoken.html'
            extra_context['hide'] = True
        else:
            template_name = 'auth/loginviatoken.html'
    res = django_auth_views.login(request, template_name=template_name, authentication_form=form, extra_context = extra_context, **kwargs)
    if request.user.is_authentication():
        auth_user.set_session_form_user(request, request.user)
        regions = dict(forms.LoginViaToken.get_region_choices())
        region = request.user.endpoint
        region_name = region.get(region)
        request.session['region_endpoint'] = region
        request.session['region_name'] = region_name
    return res