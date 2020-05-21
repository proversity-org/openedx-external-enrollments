"""Tests api.v0.views file."""
import logging
from collections import OrderedDict
from datetime import datetime, timedelta

from django.conf import settings
from django.test import TestCase
from mock import Mock, patch
from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from testfixtures import LogCapture

from openedx_external_enrollments.api.v0.views import (
    BaseExternalEnrollment,
    EdxEnterpriseExternalEnrollment,
    EdxInstanceExternalEnrollment,
    ExternalEnrollmentFactory,
    SalesforceEnrollment,
)
from openedx_external_enrollments.models import EnrollmentRequestLog, ProgramSalesforceEnrollment


class BaseExternalEnrollmentTest(TestCase):
    """Test class for BaseExternalEnrollment class."""

    def setUp(self):
        """Set test database."""
        self.base = BaseExternalEnrollment()
        self.base.__str__ = lambda: 'test-class'

    @patch('openedx_external_enrollments.api.v0.views.requests.post')
    def test_execute_post(self, mock_post):
        """Testing _execute_post method."""
        url = 'test_url'
        data = 'data'
        headers = 'headers'
        json_data = 'json_data'

        self.base._execute_post(
            url=url,
            data=data,
            headers=headers,
            json_data=json_data,
        )
        mock_post.assert_called_with(
            url=url,
            data=data,
            headers=headers,
            json=json_data,
        )

    @patch.object(BaseExternalEnrollment, '_get_enrollment_url')
    @patch.object(BaseExternalEnrollment, '_get_enrollment_headers')
    @patch.object(BaseExternalEnrollment, '_get_enrollment_data')
    @patch.object(BaseExternalEnrollment, '_execute_post')
    def test_post_enrollment(self, post_mock, data_mock, headers_mock, url_mock):
        """Testing _post_enrollment method."""
        data = {'test': 'data'}
        headers = {'headers': 'test'}
        url = 'https://fake-testing.com'
        course_settings = {'course': 'settings'}
        url_mock.return_value = url
        data_mock.return_value = data
        post_mock.return_value.json.return_value = data
        headers_mock.return_value = headers

        log1 = 'calling enrollment for [{}] with data: {}'.format(self.base.__str__(), data)
        log2 = 'calling enrollment for [{}] with url: {}'.format(self.base.__str__(), url)
        log3 = 'calling enrollment for [{}] with course settings: {}'.format(self.base.__str__(), course_settings)

        with LogCapture(level=logging.INFO) as log_capture:
            response = self.base._post_enrollment(data, course_settings)
            log4 = 'External enrollment response for [{}] -- {}'.format(self.base.__str__(), data)
            log_capture.check(
                ('openedx_external_enrollments.api.v0.views', 'INFO', log1),
                ('openedx_external_enrollments.api.v0.views', 'INFO', log2),
                ('openedx_external_enrollments.api.v0.views', 'INFO', log3),
                ('openedx_external_enrollments.api.v0.views', 'INFO', log4),
            )

        self.assertEqual(response, (data, status.HTTP_200_OK))
        url_mock.assert_called_with(course_settings)
        data_mock.assert_called_with(data, course_settings)
        post_mock.assert_called_with(
            url=url,
            headers=headers,
            json_data=data,
        )

        log_details = {
            'request_payload': data,
            'url': url,
            'course_advanced_settings': course_settings,
            'response': data,
        }

        request_log = EnrollmentRequestLog.objects.filter(request_type=str(self.base), details=log_details)
        self.assertEqual(len(request_log), 1)

        headers_mock.side_effect = NotImplementedError('My test error')

        with LogCapture(level=logging.INFO) as log_capture:
            response = self.base._post_enrollment(data, course_settings)
            log4 = 'Failed to complete enrollment. Reason: {}'.format('My test error')
            log_capture.check(
                ('openedx_external_enrollments.api.v0.views', 'INFO', log1),
                ('openedx_external_enrollments.api.v0.views', 'INFO', log2),
                ('openedx_external_enrollments.api.v0.views', 'INFO', log3),
                ('openedx_external_enrollments.api.v0.views', 'ERROR', log4),
            )

        log_details['response'] = {'error': log4}
        request_log = EnrollmentRequestLog.objects.filter(request_type=str(self.base), details=log_details)
        self.assertEqual(len(request_log), 1)

    def test_get_enrollment_data(self):
        """Testing _get_enrollment_data method."""
        self.assertRaises(NotImplementedError, self.base._get_enrollment_data)

    def test_get_enrollment_headers(self):
        """Testing _get_enrollment_headers method."""
        self.assertRaises(NotImplementedError, self.base._get_enrollment_headers)

    def test_get_enrollment_url(self):
        """Testing _get_enrollment_url method."""
        self.assertRaises(NotImplementedError, self.base._get_enrollment_url)


class EdxEnterpriseExternalEnrollmentTest(TestCase):
    """Test class for EdxEnterpriseExternalEnrollment class."""

    def setUp(self):
        """Set test database."""
        self.base = EdxEnterpriseExternalEnrollment()

    def test_get_enrollment_data(self):
        """Testing _get_enrollment_data method."""
        data = {
            'course_mode': 'first_mode',
            'user_email': 'test_email',
        }
        course_settings = {
            'external_course_run_id': 'test_course_run_id',
            'external_enrollment_mode_override': 'test_mode',
        }
        expected_data = {
            'course_run_id': 'test_course_run_id',
            'course_mode': 'test_mode',
            'user_email': 'test_email',
            'is_active': True,
        }

        self.assertEqual(
            self.base._get_enrollment_data(data, course_settings),
            [expected_data],
        )

        del course_settings['external_enrollment_mode_override']
        expected_data['course_mode'] = data['course_mode']

        self.assertEqual(
            self.base._get_enrollment_data(data, course_settings),
            [expected_data],
        )

        expected_data = {key: None for key in expected_data}
        expected_data['is_active'] = True

        self.assertEqual(
            self.base._get_enrollment_data({}, {}),
            [expected_data],
        )

    @patch.object(EdxEnterpriseExternalEnrollment, '_execute_post')
    def test_get_enrollment_headers(self, post_mock):
        """Testing _get_enrollment_headers method."""
        data = OrderedDict(
            grant_type="client_credentials",
            client_id=settings.EDX_ENTERPRISE_API_CLIENT_ID,
            client_secret=settings.EDX_ENTERPRISE_API_CLIENT_SECRET,
            token_type="jwt",
        )
        post_mock.return_value.json.return_value = {
            'token_type': 'test-token-type',
            'access_token': 'test-access-token',
        }
        expected_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'test-token-type test-access-token',
        }

        self.assertEqual(self.base._get_enrollment_headers(), expected_headers)
        post_mock.assert_called_with(settings.EDX_ENTERPRISE_API_TOKEN_URL, data)

        post_mock.return_value.ok = False
        self.assertIsNone(self.base._get_enrollment_headers())

        with LogCapture(level=logging.INFO) as log_capture:
            post_mock.side_effect = Exception('test-exception')
            self.assertIsNone(self.base._get_enrollment_headers())
            log_capture.check(
                ('openedx_external_enrollments.api.v0.views', 'ERROR', 'Failed to get token: test-exception'),
            )

    def test_get_enrollment_url(self):
        """Testing _get_enrollment_url method."""
        expected_url = '{}/enterprise-customer/{}/course-enrollments'.format(
            settings.EDX_ENTERPRISE_API_BASE_URL,
            settings.EDX_ENTERPRISE_API_CUSTOMER_UUID,
        )
        self.assertEqual(
            expected_url,
            self.base._get_enrollment_url(course_settings={}),
        )

    def test_str(self):
        """
        EdxEnterpriseExternalEnrollment overrides the __str__ method,
        this test that the method __str__ returns the right value.
        """
        self.assertEqual(
            'edX',
            self.base.__str__(),
        )


class EdxInstanceExternalEnrollmentTest(TestCase):
    """Test class for EdxInstanceExternalEnrollment class."""

    def setUp(self):
        """Set test database."""
        self.base = EdxInstanceExternalEnrollment()

    @patch('openedx_external_enrollments.api.v0.views.get_user')
    def test_get_enrollment_data(self, get_user_mock):
        """Testing _get_enrollment_data method."""
        data = {
            'course_mode': 'first_mode',
            'user_email': 'test_email',
        }
        course_settings = {
            'external_course_run_id': 'test_course_run_id',
            'external_enrollment_mode_override': 'test_mode',
        }
        expected_data = {
            'user': 'test-username',
            'mode': 'test_mode',
            'is_active': True,
            'course_details': {
                'course_id': 'test_course_run_id',
            },
        }

        user = Mock()
        user.username = 'test-username'
        get_user_mock.return_value = (user, '')

        self.assertEqual(
            self.base._get_enrollment_data(data, course_settings),
            expected_data,
        )

        del course_settings['external_enrollment_mode_override']
        expected_data['mode'] = data['course_mode']

        self.assertEqual(
            self.base._get_enrollment_data(data, course_settings),
            expected_data,
        )

        expected_data['mode'] = None
        expected_data['course_details']['course_id'] = None

        self.assertEqual(
            self.base._get_enrollment_data({}, {}),
            expected_data,
        )

    def test_get_enrollment_headers(self):
        """Testing _get_enrollment_headers method."""
        expected_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Edx-Api-Key": settings.EDX_API_KEY,
        }

        self.assertEqual(self.base._get_enrollment_headers(), expected_headers)

    def test_get_enrollment_url(self):
        """Testing _get_enrollment_url method."""
        expected_url = 'https://edx-external-instance.com/api/v0/enrollments'
        course_settings = {
            'external_enrollment_api_url': expected_url,
        }
        self.assertIsNone(
            self.base._get_enrollment_url(course_settings={}),
        )
        self.assertEqual(
            expected_url,
            self.base._get_enrollment_url(course_settings),
        )

    def test_str(self):
        """
        EdxInstanceExternalEnrollment overrides the __str__ method,
        this test that the method __str__ returns the right value.
        """
        self.assertEqual(
            'openedX',
            self.base.__str__(),
        )


class SalesforceEnrollmentTest(TestCase):
    """Test class for SalesforceEnrollment class."""

    def setUp(self):
        """Set test database."""
        self.base = SalesforceEnrollment()

    @patch('openedx_external_enrollments.api.v0.views.get_course_by_id')
    def test_get_course(self, get_course_by_id_mock):
        """Testing _get_course method."""
        self.assertIsNone(
            self.base._get_course(''),
        )

        course_id = 'course-v1:test+CS102+2019_T3'
        course_key = CourseKey.from_string(course_id)
        expected_course = 'test-course'
        get_course_by_id_mock.return_value = expected_course

        self.assertEqual(self.base._get_course(course_id), expected_course)
        get_course_by_id_mock.assert_called_once_with(course_key)

    def test_str(self):
        """
        SalesforceEnrollment overrides the __str__ method,
        this test that the method __str__ returns the right value.
        """
        self.assertEqual(
            'salesforce',
            self.base.__str__(),
        )

    @patch.object(SalesforceEnrollment, '_get_auth_token')
    def test_get_enrollment_headers(self, get_auth_token_mock):
        """Testing _get_enrollment_headers method."""

        get_auth_token_mock.return_value = {
            'token_type': 'test-token-type',
            'access_token': 'test-access-token',
        }
        expected_headers = {
            'Content-Type': 'application/json',
            'Authorization': 'test-token-type test-access-token',
        }
        self.assertEqual(self.base._get_enrollment_headers(), expected_headers)
        get_auth_token_mock.assert_called_once()

    @patch('openedx_external_enrollments.api.v0.views.OAuth2Session')
    @patch('openedx_external_enrollments.api.v0.views.BackendApplicationClient')
    def test_get_auth_token(self, backend_mock, oauth_session_mock):
        """Testing _get_auth_token method."""
        oauth_mock = Mock()
        oauth_mock.fetch_token.return_value = 'test-token'
        backend_mock.return_value = 'test-client'
        oauth_session_mock.return_value = oauth_mock

        request_params = {
            'client_id': settings.SALESFORCE_API_CLIENT_ID,
            'client_secret': settings.SALESFORCE_API_CLIENT_SECRET,
            'username': settings.SALESFORCE_API_USERNAME,
            'password': settings.SALESFORCE_API_PASSWORD,
            'grant_type': 'password',
        }

        self.assertEqual('test-token', self.base._get_auth_token())
        backend_mock.assert_called_once_with(**request_params)
        oauth_session_mock.assert_called_once_with(client='test-client')
        oauth_mock.fetch_token.assert_called_once_with(token_url=settings.SALESFORCE_API_TOKEN_URL)

    @patch('openedx_external_enrollments.api.v0.views.get_user')
    def test_get_openedx_user(self, get_user_mock):
        """Testing _get_openedx_user method."""
        self.assertEqual({}, self.base._get_openedx_user(data={}))

        data = {
            'supported_lines': [
                {'user_email': 'test-email'},
            ],
        }
        expected_user = {
            'FirstName': 'Peter',
            'LastName': 'Parker',
            'Email': 'test-email',
        }
        profile_mock = Mock()
        profile_mock.name = 'Peter Parker'
        get_user_mock.return_value = (Mock(), profile_mock)

        self.assertEqual(expected_user, self.base._get_openedx_user(data))
        get_user_mock.assert_called_once_with(email='test-email')

        get_user_mock.side_effect = Exception('test')
        self.assertEqual({}, self.base._get_openedx_user(data))

    @patch.object(SalesforceEnrollment, '_get_program_of_interest_data')
    def test_get_salesforce_data(self, get_program_mock):
        """Testing _get_salesforce_data method."""
        data = {
            'supported_lines': [],
            'program': False,
            'paid_amount': 100,
            'currency': 'USD',
        }

        self.assertEqual({}, self.base._get_salesforce_data(data))

        lines = [
            {'user_email': 'test-email'},
        ]
        expected_data = {
            'Purchase_Type': 'Course',
            'PaymentAmount': 100,
            'Amount_Currency': 'USD',
        }
        program_data = {
            'test-key': 'test-value',
            'test-key1': 'test-value1',
            'test-key2': 'test-value2',
        }
        data['supported_lines'] = lines
        expected_data.update(program_data)
        get_program_mock.return_value = program_data

        self.assertEqual(expected_data, self.base._get_salesforce_data(data))
        get_program_mock.assert_called_once_with(data, lines)

        data['program'] = True
        expected_data['Purchase_Type'] = 'Program'
        self.assertEqual(expected_data, self.base._get_salesforce_data(data))

        get_program_mock.side_effect = Exception('test')
        self.assertEqual({}, self.base._get_salesforce_data(data))

    @patch('openedx_external_enrollments.api.v0.views.get_user')
    @patch.object(SalesforceEnrollment, '_get_course')
    def test_get_program_of_interest_data(self, get_course_mock, get_user_mock):
        """Testing _get_program_of_interest_data method."""
        self.assertEqual({}, self.base._get_program_of_interest_data({}, []))

        lines = [
            {
                'user_email': 'test-email',
                'course_id': 'test-course-id',
            },
        ]
        data = {
            'supported_lines': lines,
            'program': {},
        }
        expected_data = {
            'Lead_Source': 'Undefined',
            'Secondary_Source': 'Undefined',
            'Tertiary_Source': 'Undefined',
        }
        course_mock = Mock()
        course_mock.other_course_settings = {'salesforce_data': {}}
        get_course_mock.return_value = course_mock
        user_mock = Mock()
        user_mock.username = 'Spiderman'
        get_user_mock.return_value = (user_mock, Mock())
        expected_drupal = 'enrollment+course+{}+{}'.format(
            user_mock.username,
            datetime.utcnow().strftime('%Y-%m-%d-%H:%M'),
        )

        program_data = self.base._get_program_of_interest_data(data, lines)
        get_user_mock.assert_called_with(email='test-email')
        get_course_mock.assert_called_with('test-course-id')

        drupal_id = program_data.pop('Drupal_ID')
        self.assertEqual(expected_data, program_data)
        self.assertTrue(drupal_id.startswith(expected_drupal))

        salesforce_data = {
            'Lead_Source': 'test-lead',
            'Secondary_Source': 'test-secondary',
            'Tertiary_Source': 'test-tertiary',
        }
        expected_data.update(salesforce_data)
        course_mock.other_course_settings = {'salesforce_data': salesforce_data}

        program_data = self.base._get_program_of_interest_data(data, lines)
        drupal_id = program_data.pop('Drupal_ID')
        self.assertEqual(expected_data, program_data)

        data['program'] = {'uuid': 'test-uuid'}
        data['utm_source'] = 'test-source'
        expected_data['Lead_Source'] = data['utm_source']
        expected_drupal = 'enrollment+program+{}+{}'.format(
            user_mock.username,
            datetime.utcnow().strftime('%Y/%m/%d-%H:%M'),
        )
        ProgramSalesforceEnrollment.objects.create(bundle_id='test-uuid', meta=salesforce_data)
        program_data = self.base._get_program_of_interest_data(data, lines)
        drupal_id = program_data.pop('Drupal_ID')
        self.assertEqual(expected_data, program_data)
        self.assertTrue(drupal_id.startswith(expected_drupal))

    @patch.object(SalesforceEnrollment, '_get_salesforce_course_id')
    @patch.object(SalesforceEnrollment, '_get_course_start_date')
    @patch.object(SalesforceEnrollment, '_get_course')
    def test_get_courses_data(self, get_course_mock, get_date_mock, get_salesforce_mock):
        """Testing _get_courses_data method."""
        self.assertEqual([], self.base._get_courses_data({}, []))

        lines = [
            {
                'user_email': 'test-email',
                'course_id': 'test-course-id',
            },
        ]
        now = datetime.now()
        course_mock = Mock()
        course_mock.end = now
        course_mock.display_name = 'test-course'
        course_mock.other_course_settings = {'salesforce_data': {}}
        get_course_mock.return_value = course_mock
        get_date_mock.return_value = now
        get_salesforce_mock.return_value = 'test-salesforce'
        expected_data = {
            'CourseName': course_mock.display_name,
            'CourseCode': 'test-salesforce',
            'CourseStartDate': now,
            'CourseEndDate': now.strftime('%Y-%m-%d'),
            'CourseDuration': '0',
        }

        self.assertEqual([expected_data], self.base._get_courses_data({}, lines))
        get_course_mock.assert_called_with('test-course-id')
        get_date_mock.assert_called_with(course_mock, 'test-email', 'test-course-id')

        course_mock.other_course_settings = {
            'salesforce_data': {
                'Program_Name': 'test-program',
            },
        }
        expected_data['CourseName'] = 'test-program'

        self.assertEqual([expected_data], self.base._get_courses_data({}, lines))

        get_course_mock.side_effect = Exception('test-exception')

        self.assertEqual([], self.base._get_courses_data({}, lines))

    @patch.object(SalesforceEnrollment, '_is_external_course')
    def test_get_salesforce_course_id(self, external_course_mock):
        """Testing _get_salesforce_course_id method."""
        external_course_mock.return_value = False
        course_mock = Mock()
        course_mock.other_course_settings = {'external_course_run_id': 'test-settings-id'}

        self.assertEqual('internal-id', self.base._get_salesforce_course_id(course_mock, 'internal-id'))
        external_course_mock.assert_called_with(course_mock)

        external_course_mock.return_value = True
        self.assertEqual(
            'test-settings-id',
            self.base._get_salesforce_course_id(course_mock, 'internal-id'),
        )

    def test_is_external_course(self):
        """Testing _is_external_course method."""
        course_mock = Mock()
        course_mock.other_course_settings = {}
        self.assertFalse(self.base._is_external_course(course_mock))

        course_mock.other_course_settings = {'external_course_run_id': 'test'}
        self.assertFalse(self.base._is_external_course(course_mock))

        course_mock.other_course_settings = {'external_course_target': 'test'}
        self.assertFalse(self.base._is_external_course(course_mock))

        course_mock.other_course_settings = {
            'external_course_target': 'test',
            'external_course_run_id': 'test',
        }
        self.assertTrue(self.base._is_external_course(course_mock))

    @patch('openedx_external_enrollments.api.v0.views.get_user')
    @patch('openedx_external_enrollments.api.v0.views.CourseEnrollment')
    def test_get_course_start_date(self, enrollment_mock, get_user_mock):
        """Testing _get_course_start_date method."""
        now = datetime.now()
        course_mock = Mock()
        course_mock.start = now - timedelta(days=1)
        course_mock.self_paced = True
        user = Mock()
        get_user_mock.return_value = (user, Mock())
        course_id = 'course-v1:test+CS102+2019_T3'
        course_key = CourseKey.from_string(course_id)
        enrollment = Mock()
        enrollment.created = now
        enrollment_mock.get_enrollment.return_value = enrollment

        self.assertEqual(
            now.strftime('%Y-%m-%d'),
            self.base._get_course_start_date(course_mock, 'test-email', course_id),
        )
        enrollment_mock.get_enrollment.assert_called_with(user, course_key)

        course_mock.self_paced = False
        self.assertEqual(
            (now - timedelta(days=1)).strftime('%Y-%m-%d'),
            self.base._get_course_start_date(course_mock, 'test-email', course_id),
        )

    @patch.object(SalesforceEnrollment, '_get_salesforce_data')
    @patch.object(SalesforceEnrollment, '_get_openedx_user')
    @patch.object(SalesforceEnrollment, '_get_courses_data')
    def test_get_enrollment_data(self, get_course_mock, get_openedx_mock, get_salesforce_mock):
        """Testing _get_enrollment_data method."""
        now = datetime.now()
        lines = [
            {'user_email': 'test-email'},
        ]
        data = {
            'test': 'data',
            'supported_lines': lines,
        }
        user_data = {
            'FirstName': 'Peter',
            'LastName': 'Parker',
            'Email': 'test-email',
        }
        salesforce_data = {
            'Lead_Source': 'test-source',
            'Secondary_Source': 'Undefined',
            'Tertiary_Source': 'Undefined',
        }
        course_data = {
            'CourseName': 'test-course-name',
            'CourseCode': 'test-code',
            'CourseStartDate': now,
            'CourseEndDate': now.strftime('%Y-%m-%d'),
            'CourseDuration': '0',
        }
        get_openedx_mock.return_value = user_data
        get_salesforce_mock.return_value = salesforce_data
        get_course_mock.return_value = course_data

        enrollment = {}
        enrollment.update(user_data)
        enrollment.update(salesforce_data)
        enrollment['Course_Data'] = course_data
        expected_data = {
            'enrollment': enrollment,
        }
        self.assertEqual(expected_data, self.base._get_enrollment_data(data, {}))
        get_openedx_mock.assert_called_once_with(data)
        get_salesforce_mock.assert_called_once_with(data)
        get_course_mock.assert_called_once_with(data, lines)

        user_data['unwanted_key'] = 'testing'
        get_openedx_mock.return_value = user_data
        self.assertEqual(expected_data, self.base._get_enrollment_data(data, {}))

    @patch.object(SalesforceEnrollment, '_get_auth_token')
    def test_get_enrollment_url(self, get_auth_token_mock):
        """Testing _get_enrollment_url method."""
        get_auth_token_mock.return_value = {
            'token_type': 'test-token-type',
            'access_token': 'test-access-token',
            'instance_url': 'test-instance-url',
        }
        expected_url = '{}/{}'.format('test-instance-url', settings.SALESFORCE_ENROLLMENT_API_PATH)
        self.assertEqual(expected_url, self.base._get_enrollment_url({}))
        get_auth_token_mock.assert_called_once()


class ExternalEnrollmentFactoryTest(TestCase):
    """Test class for ExternalEnrollmentFactory class."""

    def test_get_enrollment_controller(self):
        """Testing _get_enrollment_controller method."""
        controller = 'edX'
        self.assertTrue(
            isinstance(
                ExternalEnrollmentFactory.get_enrollment_controller(controller),
                EdxEnterpriseExternalEnrollment,
            )
        )
        controller = 'openedX'
        self.assertTrue(
            isinstance(
                ExternalEnrollmentFactory.get_enrollment_controller(controller),
                EdxInstanceExternalEnrollment,
            )
        )
