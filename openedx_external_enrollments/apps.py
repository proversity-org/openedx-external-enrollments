"""
App configuration for openedx_external_enrollments.
"""

from __future__ import unicode_literals

from django.apps import AppConfig


class OpenedxExternalEnrollmentConfig(AppConfig):
    """
    External Enrollments configuration.
    """
    name = 'openedx_external_enrollments'
    verbose_name = 'External Enrollments'

    plugin_app = {
        'url_config': {
            'lms.djangoapp': {
                'namespace': 'openedx_external_enrollments',
                'regex': r'^openedx_external_enrollments/',
                'relative_path': 'urls',
            },
            'cms.djangoapp': {
                'namespace': 'openedx_external_enrollments',
                'regex': r'^openedx_external_enrollments/',
                'relative_path': 'urls',
            }
        },
        'settings_config': {
            'lms.djangoapp': {
                'common': {'relative_path': 'settings.common'},
                'test': {'relative_path': 'settings.test'},
                'aws': {'relative_path': 'settings.aws'},
                'production': {'relative_path': 'settings.production'},
            },
            'cms.djangoapp': {
                'common': {'relative_path': 'settings.common'},
                'test': {'relative_path': 'settings.test'},
                'aws': {'relative_path': 'settings.aws'},
                'production': {'relative_path': 'settings.production'},
            },
        },
        'signals_config': {
            'lms.djangoapp': {
                'relative_path': 'signal_receivers',
                'receivers': [
                    {
                        'receiver_func_name': 'update_external_enrollment',
                        'signal_path': 'django.db.models.signals.post_save',
                        'dispatch_uid': 'update_external_enrollment_receiver',
                        'sender_path': 'student.models.CourseEnrollment',
                    },
                    {
                        'receiver_func_name': 'delete_external_enrollment',
                        'signal_path': 'django.db.models.signals.post_delete',
                        'dispatch_uid': 'delete_external_enrollment_receiver',
                        'sender_path': 'student.models.CourseEnrollment',
                    },
                ],
            },
        },
    }

    def ready(self):
        """
        The line below allows tasks defined in this app to be included by celery workers.
        https://docs.djangoproject.com/en/1.8/ref/applications/#methods
        """
        from openedx_external_enrollments.api.v0.views import (  # pylint: disable=unused-variable
            generate_salesforce_enrollment,
        )
