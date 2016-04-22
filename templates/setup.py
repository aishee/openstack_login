from setuptools import setup

setup(
    name='openstack_auth_token',
    version='1.0',
    description='Module for logging into Horizon via token',
    author='Aishee Nguyen',
    author_email='aishee@aishee.net',
    url='https://github.com/aishee/openstack_login',
    packages=['openstack_auth_token'],
    package_data={'openstack_auth_token':['templates/*']},
)