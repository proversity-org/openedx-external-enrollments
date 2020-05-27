"""EdxEnterpriseExternalEnrollment class file."""
import logging
from collections import OrderedDict

from django.conf import settings

from openedx_external_enrollments.external_enrollments.base_external_enrollment import BaseExternalEnrollment

LOG = logging.getLogger(__name__)


class EdxEnterpriseExternalEnrollment(BaseExternalEnrollment):
    """
    """

    def __str__(self):
        return "edX"

    def _get_enrollment_headers(self):
        """
        """
        try:
            data = OrderedDict(
                grant_type="client_credentials",
                client_id=settings.EDX_ENTERPRISE_API_CLIENT_ID,
                client_secret=settings.EDX_ENTERPRISE_API_CLIENT_SECRET,
                token_type="jwt",
            )
            response = self._execute_post(
                settings.EDX_ENTERPRISE_API_TOKEN_URL,
                data,
            )
        except Exception as error:
            LOG.error("Failed to get token: " + str(error))
        else:
            if response.ok:
                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": "{} {}".format(
                        response.json()["token_type"],
                        response.json()["access_token"]
                    )
                }
                return headers

    def _get_enrollment_data(self, data, course_settings):

        return [{
            "course_run_id": course_settings.get(
                "external_course_run_id",
            ),
            "course_mode": course_settings.get(
                "external_enrollment_mode_override",
                data.get("course_mode"),
            ),
            "user_email": data.get("user_email"),
            "is_active": True,
        }]

    def _get_enrollment_url(self, course_settings):
        """
        """
        api_resource = "/enterprise-customer/{}/course-enrollments".format(settings.EDX_ENTERPRISE_API_CUSTOMER_UUID)
        return "{}{}".format(settings.EDX_ENTERPRISE_API_BASE_URL, api_resource)
