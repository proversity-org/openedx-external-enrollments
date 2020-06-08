"""Openedx external enrollments receivers file."""
from openedx_external_enrollments.edxapp_wrapper.get_courseware import get_course_by_id
from openedx_external_enrollments.edxapp_wrapper.get_site_configuration import configuration_helpers
from openedx_external_enrollments.external_enrollments import execute_external_enrollment


def update_external_enrollment(sender, created, instance, **kwargs):  # pylint: disable=unused-argument
    """
    This receiver is called when the django.db.models.signals.post_save signal is sent,
    it will execute an enrollment or unenrollment based on the value of instance.is_active.
    """
    if (not configuration_helpers.get_value('ENABLE_EXTERNAL_ENROLLMENTS', False)
            or (created and not instance.is_active)):
        return

    data = {
        'user_email': instance.user.email,
        'course_mode': instance.mode,
        'is_active': instance.is_active,
    }

    execute_external_enrollment(data=data, course=get_course_by_id(instance.course.id))


def delete_external_enrollment(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    This receiver is called when the django.db.models.signals.post_delete signal is sent,
    it will always execute an unenrollment.
    """
    if not configuration_helpers.get_value('ENABLE_EXTERNAL_ENROLLMENTS', False):
        return

    data = {
        'user_email': instance.user.email,
        'course_mode': instance.mode,
        'is_active': False,
    }

    execute_external_enrollment(data=data, course=get_course_by_id(instance.course.id))
