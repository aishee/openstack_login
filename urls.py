from django.conf.urls import patterns
from django.conf.urls import url

from openstack_auth import utils

urlpatterns = patterns(
    'openstack_auth_token_views',
    url(r"^token/$", 'token', name='token')
)