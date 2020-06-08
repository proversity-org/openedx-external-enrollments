"""Tests EdxEnterpriseExternalEnrollment class file."""
import logging
from collections import OrderedDict

from django.conf import settings
from django.test import TestCase
from mock import patch
from testfixtures import LogCapture

from openedx_external_enrollments.external_enrollments.edx_enterprise_external_enrollment import (
    EdxEnterpriseExternalEnrollment,
)

module = 'openedx_external_enrollments.external_enrollments.edx_enterprise_external_enrollment'


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
            self.base._get_enrollment_data(data, course_settings),  # pylint: disable=protected-access
            [expected_data],
        )

        del course_settings['external_enrollment_mode_override']
        expected_data['course_mode'] = data['course_mode']

        self.assertEqual(
            self.base._get_enrollment_data(data, course_settings),  # pylint: disable=protected-access
            [expected_data],
        )

        expected_data = {key: None for key in expected_data}
        expected_data['is_active'] = True

        self.assertEqual(
            self.base._get_enrollment_data({}, {}),  # pylint: disable=protected-access
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

        self.assertEqual(self.base._get_enrollment_headers(), expected_headers)  # pylint: disable=protected-access
        post_mock.assert_called_with(settings.EDX_ENTERPRISE_API_TOKEN_URL, data)

        post_mock.return_value.ok = False
        self.assertIsNone(self.base._get_enrollment_headers())  # pylint: disable=protected-access

        with LogCapture(level=logging.INFO) as log_capture:
            post_mock.side_effect = Exception('test-exception')
            self.assertIsNone(self.base._get_enrollment_headers())  # pylint: disable=protected-access
            log_capture.check(
                (module, 'ERROR', 'Failed to get token: test-exception'),
            )

    def test_get_enrollment_url(self):
        """Testing _get_enrollment_url method."""
        expected_url = '{}/enterprise-customer/{}/course-enrollments'.format(
            settings.EDX_ENTERPRISE_API_BASE_URL,
            settings.EDX_ENTERPRISE_API_CUSTOMER_UUID,
        )
        self.assertEqual(
            expected_url,
            self.base._get_enrollment_url(course_settings={}),  # pylint: disable=protected-access
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
