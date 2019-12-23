"""
This file contains the views for openedx-external-enrollments API.
"""
import requests
import json
import logging
from collections import OrderedDict

from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.models import User
from opaque_keys.edx.keys import CourseKey
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework_oauth.authentication import OAuth2Authentication

from courseware.courses import get_course_by_id
from openedx_external_enrollments.edxapp_wrapper.get_edx_rest_framework_extensions import (
    get_jwt_authentication,
)
from openedx_external_enrollments.edxapp_wrapper.get_openedx_permissions import (
    get_api_key_permission,
)
from student.models import get_user

LOG = logging.getLogger(__name__)


class ExternalEnrollment(APIView):

    authentication_classes = [
        get_jwt_authentication(),
        OAuth2Authentication,
    ]
    permission_classes = [
        get_api_key_permission(),
    ]

    def post(self, request):
        """
        View to execute the external enrollment.
        """
        response = {}
        course = self._get_course(request.data.get("course_id"))

        if not course:
            return JsonResponse(
                {"error": "Invalid operation: course not found" },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Getting the corresponding enrollment controller
            enrollment_controller = ExternalEnrollmentFactory.get_enrollment_controller(
                course.other_course_settings.get("external_platform_target")
            )
        except Exception:
            LOG.info('Course [%s] not configured as external', request.data.get("course_id"))
            return JsonResponse(
                {"info": "Course {} not configured as external".format(request.data.get("course_id"))},
                status=status.HTTP_200_OK,
            )
        else:
            # Now, let's try to execute the enrollment
            response, request_status = enrollment_controller._post_enrollment(request.data, course.other_course_settings)

        return JsonResponse(response, status=request_status, safe=False)

    @staticmethod
    def _get_course(course_id):
        """
        Return a course object.
        """
        if not course_id:
            return None

        course_key = CourseKey.from_string(course_id)
        course = get_course_by_id(course_key)
        return course


class BaseExternalEnrollment(object):
    """
    """
    def _execute_post(self, url, data=None, headers=None, json=None):
        """
        """
        response = requests.post(
            url=url,
            data=data,
            headers=headers,
            json=json,
        )
        return response

    def _post_enrollment(self, data, course_settings):
        """
        """
        url = self._get_enrollment_url(course_settings)
        json = self._get_enrollment_data(data, course_settings)
        LOG.info('calling enrollment for [%s] with data: %s', self.__str__(), json)
        LOG.info('calling enrollment for [%s] with url: %s', self.__str__(), url)
        LOG.info('calling enrollment for [%s] with course settings: %s', self.__str__(), course_settings)

        try:
            response = self._execute_post(
                url=url,
                headers=self._get_enrollment_headers(),
                json=json,
            )
        except Exception as error:
            LOG.error("Failed to complete enrollment. Reason: "+ str(error))
            return str(error), status.HTTP_400_BAD_REQUEST
        else:
            LOG.info('External enrollment response for [%s] -- %s', self.__str__(), response.json())
            return response.json(), status.HTTP_200_OK


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
            LOG.error("Failed to get token: "+ str(error))
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


class EdxInstanceExternalEnrollment(BaseExternalEnrollment):
    """
    """

    def __str__(self):
        return "openedX instance"

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


class ExternalEnrollmentFactory:
    """
    """
    @classmethod
    def get_enrollment_controller(cls, controller):
        """
        Return the an instance of the enrollment controller.
        """
        if controller.lower() == 'openedx':
            return EdxInstanceExternalEnrollment()
        else:
            return EdxEnterpriseExternalEnrollment()
