"""
Common Django settings for openedx_external_enrollments project.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

from __future__ import unicode_literals

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'secret-key'


# Application definition

INSTALLED_APPS = []

ROOT_URLCONF = 'openedx_external_enrollments.urls'


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_TZ = True


def plugin_settings(settings):
    """
    Set of plugin settings used by the Open Edx platform.
    More info: https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/plugins/README.rst
    """
    settings.OEE_EDX_REST_FRAMEWORK_EXTENSIONS = 'openedx_external_enrollments.edxapp_wrapper.backends.edx_rest_framework_extensions_i_v1'
    settings.OEE_OPENEDX_PERMISSIONS = 'openedx_external_enrollments.edxapp_wrapper.backends.openedx_permissions_i_v1'
    settings.OEE_COURSE_HOME_MODULE = 'openedx_external_enrollments.edxapp_wrapper.backends.course_home_i_v1'
    settings.OEE_COURSE_HOME_CALCULATOR = 'openedx_external_enrollments.edxapp_wrapper.get_course_home.calculate_course_home'
    settings.EDX_ENTERPRISE_API_CLIENT_ID = "client-id"
    settings.EDX_ENTERPRISE_API_CLIENT_SECRET = "client-secret"
    settings.EDX_ENTERPRISE_API_TOKEN_URL = "https://api.edx.org/oauth2/v1/access_token"
    settings.EDX_ENTERPRISE_API_BASE_URL = "https://api.edx.org/enterprise/v1"
    settings.EDX_ENTERPRISE_API_CUSTOMER_UUID = "a3554467-071a-46b1-9971-e763879ce390"
    settings.EDX_ENTERPRISE_API_CATALOG_UUID = "fba82d04-c4a4-4900-a661-c95a41d7fd1c"