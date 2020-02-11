"""
Production Django settings for openedx_external_enrollments project.
"""

from __future__ import unicode_literals


def plugin_settings(settings):
    """
    Set of plugin settings used by the Open Edx platform.
    More info: https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/plugins/README.rst
    """
    settings.EDX_ENTERPRISE_API_CLIENT_ID = getattr(settings, 'ENV_TOKENS', {}).get(
        'EDX_ENTERPRISE_API_CLIENT_ID',
        settings.EDX_ENTERPRISE_API_CLIENT_ID
    )
    settings.EDX_ENTERPRISE_API_CLIENT_SECRET = getattr(settings, 'ENV_TOKENS', {}).get(
        'EDX_ENTERPRISE_API_CLIENT_SECRET',
        settings.EDX_ENTERPRISE_API_CLIENT_SECRET
    )
    settings.EDX_ENTERPRISE_API_CUSTOMER_UUID = getattr(settings, 'ENV_TOKENS', {}).get(
        'EDX_ENTERPRISE_API_CUSTOMER_UUID',
        settings.EDX_ENTERPRISE_API_CUSTOMER_UUID
    )
    settings.EDX_ENTERPRISE_API_CATALOG_UUID = getattr(settings, 'ENV_TOKENS', {}).get(
        'EDX_ENTERPRISE_API_CATALOG_UUID',
        settings.EDX_ENTERPRISE_API_CATALOG_UUID
    )
    settings.SALESFORCE_API_TOKEN_URL = getattr(settings, 'ENV_TOKENS', {}).get(
        'SALESFORCE_API_TOKEN_URL',
        settings.SALESFORCE_API_TOKEN_URL
    )
    settings.SALESFORCE_API_CLIENT_ID = getattr(settings, 'ENV_TOKENS', {}).get(
        'SALESFORCE_API_CLIENT_ID',
        settings.SALESFORCE_API_CLIENT_ID
    )
    settings.SALESFORCE_API_CLIENT_SECRET = getattr(settings, 'ENV_TOKENS', {}).get(
        'SALESFORCE_API_CLIENT_SECRET',
        settings.SALESFORCE_API_CLIENT_SECRET
    )
    settings.SALESFORCE_API_USERNAME = getattr(settings, 'ENV_TOKENS', {}).get(
        'SALESFORCE_API_USERNAME',
        settings.SALESFORCE_API_USERNAME
    )
    settings.SALESFORCE_API_PASSWORD = getattr(settings, 'ENV_TOKENS', {}).get(
        'SALESFORCE_API_PASSWORD',
        settings.SALESFORCE_API_PASSWORD
    )
