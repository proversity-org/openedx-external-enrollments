"""BaseExternalEnrollment class file."""
import logging

import requests
from rest_framework import status

from openedx_external_enrollments.models import EnrollmentRequestLog

LOG = logging.getLogger(__name__)


class BaseExternalEnrollment(object):
    """
    """
    def _execute_post(self, url, data=None, headers=None, json_data=None):
        """
        """
        response = requests.post(
            url=url,
            data=data,
            headers=headers,
            json=json_data,
        )
        return response

    def _post_enrollment(self, data, course_settings=None):
        """
        """
        url = self._get_enrollment_url(course_settings)
        json_data = self._get_enrollment_data(data, course_settings)
        LOG.info('calling enrollment for [%s] with data: %s', self.__str__(), json_data)
        LOG.info('calling enrollment for [%s] with url: %s', self.__str__(), url)
        LOG.info('calling enrollment for [%s] with course settings: %s', self.__str__(), course_settings)
        log_details = {
            "request_payload": json_data,
            "url": url,
            "course_advanced_settings": course_settings,
        }

        try:
            response = self._execute_post(
                url=url,
                headers=self._get_enrollment_headers(),
                json_data=json_data,
            )
        except Exception as error:
            LOG.error("Failed to complete enrollment. Reason: " + str(error))
            log_details["response"] = {"error": "Failed to complete enrollment. Reason: " + str(error)}
            EnrollmentRequestLog.objects.create(request_type=str(self), details=log_details)
            return str(error), status.HTTP_400_BAD_REQUEST
        else:
            LOG.info('External enrollment response for [%s] -- %s', self.__str__(), response.json())
            log_details["response"] = response.json()
            EnrollmentRequestLog.objects.create(request_type=str(self), details=log_details)
            return response.json(), status.HTTP_200_OK

    def _get_enrollment_data(course_settings):
        """Unimplemented method necessary to execute _post_enrollment."""
        raise NotImplementedError

    def _get_enrollment_headers(course_settings):
        """Unimplemented method necessary to execute _post_enrollment."""
        raise NotImplementedError

    def _get_enrollment_url(course_settings):
        """Unimplemented method necessary to execute _post_enrollment."""
        raise NotImplementedError
