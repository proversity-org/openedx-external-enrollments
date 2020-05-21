"""
This file contains the views for openedx-external-enrollments API.
"""
import datetime
import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import logging
from celery import task
from collections import OrderedDict

from django.conf import settings
from django.http import JsonResponse
from opaque_keys.edx.keys import CourseKey
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework_oauth.authentication import OAuth2Authentication

from openedx_external_enrollments.edxapp_wrapper.get_courseware import get_course_by_id
from openedx_external_enrollments.edxapp_wrapper.get_edx_rest_framework_extensions import (
    get_jwt_authentication,
)
from openedx_external_enrollments.edxapp_wrapper.get_openedx_permissions import (
    get_api_key_permission,
)
from openedx_external_enrollments.edxapp_wrapper.get_student import CourseEnrollment, get_user
from openedx_external_enrollments.models import (
    ProgramSalesforceEnrollment,
    EnrollmentRequestLog,
)


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


class SalesforceEnrollmentView(APIView):

    authentication_classes = [
        get_jwt_authentication(),
        OAuth2Authentication,
    ]
    permission_classes = [
        get_api_key_permission(),
    ]

    def post(self, request):
        """
        View to execute enrollments in salesforce.
        """
        response = {}

        try:
            # Getting the corresponding enrollment controller
            enrollment_controller = SalesforceEnrollment()
        except Exception:
            LOG.info("Can't instantiate Salesforce enrollment controller")
            return JsonResponse(
                {"info": "Can't instantiate Salesforce enrollment controller"},
                status=status.HTTP_200_OK,
            )
        else:
            # Now, let's try to call the asynchronous enrollment
            generate_salesforce_enrollment.delay(
                request.data
            )
            return JsonResponse(
                {"info": "Salesforce enrollment request sent..."},
                status=status.HTTP_200_OK,
                safe=False,
            )


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
            "request_payload" : json_data,
            "url" : url,
            "course_advanced_settings" : course_settings,
        }

        try:
            response = self._execute_post(
                url=url,
                headers=self._get_enrollment_headers(),
                json_data=json_data,
            )
        except Exception as error:
            LOG.error("Failed to complete enrollment. Reason: "+ str(error))
            log_details["response"] = { "error": "Failed to complete enrollment. Reason: "+ str(error)}
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


class SalesforceEnrollment(BaseExternalEnrollment):

    def __str__(self):
        return "salesforce"

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

    def _get_enrollment_headers(self):
        token = self._get_auth_token()
        return {
            "Content-Type": "application/json",
            "Authorization": "{} {}".format(
                token.get("token_type"),
                token.get("access_token"),
            )
        }

    @staticmethod
    def _get_auth_token():
        """

        :return:
        """
        request_params = {
            'client_id': settings.SALESFORCE_API_CLIENT_ID,
            'client_secret': settings.SALESFORCE_API_CLIENT_SECRET,
            'username': settings.SALESFORCE_API_USERNAME,
            'password': settings.SALESFORCE_API_PASSWORD,
            'grant_type': 'password',
        }
        client = BackendApplicationClient(**request_params)
        oauth = OAuth2Session(client=client)
        oauth.params = request_params
        token = oauth.fetch_token(
            token_url=settings.SALESFORCE_API_TOKEN_URL,
        )

        return token

    @staticmethod
    def _get_openedx_user(data):
        """

        :param data:
        :return:
        """
        user = {}
        order_lines = data.get("supported_lines")
        if order_lines:
            try:
                email = order_lines[0].get("user_email")
                openedx_user, openedx_profile = get_user(email=email)
                # TODO do not force logic assuming names with 2 words
                first_name, last_name = openedx_profile.name.split(" ", 1)
                user["FirstName"] = first_name.strip(" ")
                user["LastName"] = last_name.strip(" ")
                user["Email"] = email
            except Exception:
                pass

        return user

    def _get_salesforce_data(self, data):
        """

        :param data:
        :return:
        """
        salesforce_data = {}
        order_lines = data.get("supported_lines")
        if len(order_lines) > 0:
            try:
                salesforce_data.update(self._get_program_of_interest_data(data, order_lines))
                salesforce_data["Purchase_Type"] = "Program" if data.get("program") else "Course"
                salesforce_data["PaymentAmount"] = data.get("paid_amount")
                salesforce_data["Amount_Currency"] = data.get("currency")
            except Exception:
                pass

        return salesforce_data

    def _get_program_of_interest_data(self, data, order_lines):
        """

        :param data:
        :param order_lines:
        :return:
        """
        program_of_interest = {}
        program = data.get("program")
        try:
            email = order_lines[0].get("user_email")
            openedx_user, _ = get_user(email=email)
            request_time = datetime.datetime.utcnow()
            if program:
                related_program = ProgramSalesforceEnrollment.objects.get(bundle_id=program.get("uuid"))
                program_of_interest = related_program.meta
                program_of_interest["Drupal_ID"] = "enrollment+program+{}+{}".format(
                    openedx_user.username,
                    request_time.strftime("%Y/%m/%d-%H:%M:%S"),
                )
            else:
                single_course = order_lines[0]
                course = self._get_course(single_course.get("course_id"))
                program_of_interest = course.other_course_settings.get("salesforce_data")
                program_of_interest["Drupal_ID"] = "enrollment+course+{}+{}".format(
                    openedx_user.username,
                    request_time.strftime("%Y-%m-%d-%H:%M:%S"),
                )

            program_of_interest["Lead_Source"] = data.get(
                "utm_source",
                program_of_interest.get("Lead_Source", "Undefined"),
            )
            program_of_interest["Secondary_Source"] = data.get(
                "utm_campaign",
                program_of_interest.get("Secondary_Source", "Undefined"),
            )
            program_of_interest["Tertiary_Source"] = data.get(
                "utm_medium",
                program_of_interest.get("Tertiary_Source", "Undefined"),
            )
        except:
            pass

        return program_of_interest

    def _get_courses_data(self, data, order_lines):
        """

        :param data:
        :param order_lines:
        :return:
        """
        courses = []
        for line in order_lines:
            try:
                course_id = line.get("course_id")
                course = self._get_course(course_id)
                salesforce_settings = course.other_course_settings.get("salesforce_data")
                course_data = dict()
                course_data["CourseName"] = salesforce_settings.get("Program_Name") or course.display_name
                course_data["CourseCode"] = self._get_salesforce_course_id(course, course_id)
                course_data["CourseStartDate"] = self._get_course_start_date(course, line.get("user_email"), course_id)
                course_data["CourseEndDate"] = course.end.strftime("%Y-%m-%d")
                course_data["CourseDuration"] = "0"
            except:
                pass
            else:
                courses.append(course_data)


        return courses

    def _get_salesforce_course_id(self, course, internal_id):
        """
        Returns either an external course id or internal.
        """
        if self._is_external_course(course):
            return course.other_course_settings.get("external_course_run_id")

        return internal_id

    @staticmethod
    def _is_external_course(course):
        """
        True if the course was confiured as external, False otherwise.
        """

        return (
            course.other_course_settings.get("external_course_run_id") and
            course.other_course_settings.get("external_course_target")
        )

    @staticmethod
    def _get_course_start_date(course, email, course_id):
        """
        Return the course date start.
        """

        user, _ = get_user(email=email)
        course_key = CourseKey.from_string(course_id)
        enrollment = CourseEnrollment.get_enrollment(user, course_key)

        if course.self_paced:
            dates_to_check = [enrollment.created, course.start]
            student_start = max(dates_to_check)
        else:
            student_start = course.start

        return student_start.strftime("%Y-%m-%d")

    def _get_enrollment_data(self, data, course_settings):
        """
        :param data:
        :return:
        """
        valid_keys = [
            "FirstName",
            "LastName",
            "Email",
            "Company",
            "Institution_Hidden",
            "Type_Hidden",
            "Program_of_Interest",
            "Lead_Source",
            "Secondary_Source",
            "Tertiary_Source",
            "Drupal_ID",
            "Purchase_Type",
            "PaymentAmount",
            "Amount_Currency",
            "Course_Data",
        ]
        payload = {
            "enrollment": {}
        }
        openedx_user_info = self._get_openedx_user(data)
        payload["enrollment"].update(openedx_user_info)

        salesforce_data = self._get_salesforce_data(data)
        payload["enrollment"].update(salesforce_data)

        payload["enrollment"]["Course_Data"] = self._get_courses_data(
            data,
            data.get("supported_lines"),
        )

        unwanted = set(payload["enrollment"]) - set(valid_keys)
        for unwanted_key in unwanted:
            del payload["enrollment"][unwanted_key]

        return payload

    def _get_enrollment_url(self, course_settings):
        """
        """
        token = self._get_auth_token()
        return "{}/{}".format(token.get('instance_url'), settings.SALESFORCE_ENROLLMENT_API_PATH)


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


@task(default_retry_delay=5, max_retries=5)  # pylint: disable=not-callable
def generate_salesforce_enrollment(data, *args, **kwargs):
    """
    Handles the enrollment process at Salesforce.
    Args:
        data: request data
    """

    try:
        # Getting the corresponding enrollment controller
        enrollment_controller = SalesforceEnrollment()
    except Exception:
        pass
    else:
        # Calling the controller enrollment method
        response, request_status = enrollment_controller._post_enrollment(data)

    return
