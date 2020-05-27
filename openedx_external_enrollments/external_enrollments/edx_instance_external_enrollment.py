"""EdxInstanceExternalEnrollment class file."""
from django.conf import settings

from openedx_external_enrollments.edxapp_wrapper.get_student import get_user
from openedx_external_enrollments.external_enrollments.base_external_enrollment import BaseExternalEnrollment


class EdxInstanceExternalEnrollment(BaseExternalEnrollment):
    """
    """

    def __str__(self):
        return "openedX"

    def _get_enrollment_headers(self):
        """
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Edx-Api-Key": settings.EDX_API_KEY,
        }

        return headers

    def _get_enrollment_data(self, data, course_settings):
        """
        """
        user, _ = get_user(email=data.get("user_email"))
        return {
            "user": user.username,
            "is_active": True,
            "mode": course_settings.get(
                "external_enrollment_mode_override",
                data.get("course_mode")
            ),
            "course_details": {
                "course_id": course_settings.get("external_course_run_id")
            }
        }

    def _get_enrollment_url(self, course_settings):
        """
        """
        return course_settings.get("external_enrollment_api_url")
