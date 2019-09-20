"""
This file contains the views for openedx-external-enrollments API.
"""
import requests
import json
import logging
from collections import OrderedDict

from django.conf import settings
from django.http import JsonResponse, Http404
from django.contrib.auth.models import User
from opaque_keys.edx.keys import CourseKey
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework_oauth.authentication import OAuth2Authentication

from courseware.courses import get_course_by_id
from openedx_external_enrollments.edxapp_wrapper.get_edx_rest_framework_extensions import (
    get_jwt_authentication,
)
from openedx_external_enrollments.edxapp_wrapper.get_openedx_permissions import get_staff_or_owner

logger = logging.getLogger(__name__)


class ExternalEnrollment(APIView):

    authentication_classes = []
    permissions = []

    def post(self, request):
        data = request.data
        json_response = {}
        course_key = CourseKey.from_string(request.data['course_id'])
        course = get_course_by_id(course_key)
        course.other_course_settings
        data["is_active"] = True
        data["course_run_id"] = course.other_course_settings.get("external_course_run_id")
        mode_override = course.other_course_settings.get("external_enrollment_mode_override")

        if mode_override:
            data["course_mode"] = mode_override

        token = self.get_auth_token()
        if token:
            json_response = self.enroll_in_course(token, data)
        else:
            logging.info("None is an Invalid token")

        return JsonResponse(json_response, status=status.HTTP_200_OK, safe=False)

    @staticmethod
    def get_auth_token():
        data = OrderedDict(
                grant_type="client_credentials",
                client_id=settings.EDX_ENTERPRISE_API_CLIENT_ID,
                client_secret=settings.EDX_ENTERPRISE_API_CLIENT_SECRET,
                token_type="jwt",
        )
        try:
            response = requests.post(settings.EDX_ENTERPRISE_API_TOKEN_URL, data=data)
            if response.ok:
                return "{} {}".format(response.json()["token_type"], response.json()["access_token"])
        except Exception as e:
            logging.error("Failed to get token: "+ str(e))

        return None

    @staticmethod
    def enroll_in_course(token, data):
        api_resource = "/enterprise-customer/{}/course-enrollments".format(settings.EDX_ENTERPRISE_API_CUSTOMER_UUID)
        url = "{}{}".format(settings.EDX_ENTERPRISE_API_BASE_URL, api_resource)
        headers = {"Authorization": token, "Accept": "application/json", "Content-Type": "application/json"}

        try:
            logging.info('calling enrollment edx with: %s', data)
            response = requests.post(url, headers=headers, json=[data])
            if response.ok:
                data = response.json()
                logging.info("edX success external enrollment - data %s", data)
                return data
            else:
                logging.error("Error calling edX external enrollment: %s - %s", response.json(), response.reason)

        except Exception as e:
            logging.error("Failed to enroll in external course: " + str(data["course_run_id"]))
            logging.error("Reason: " + str(e))

        return {"success": False}
