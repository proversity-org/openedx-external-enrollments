"""Tests EdxInstanceExternalEnrollment class file."""
from django.conf import settings
from django.test import TestCase
from mock import Mock, patch

from openedx_external_enrollments.external_enrollments.edx_instance_external_enrollment import (
    EdxInstanceExternalEnrollment,
)


class EdxInstanceExternalEnrollmentTest(TestCase):
    """Test class for EdxInstanceExternalEnrollment class."""

    def setUp(self):
        """Set test database."""
        self.base = EdxInstanceExternalEnrollment()

    @patch('openedx_external_enrollments.external_enrollments.edx_instance_external_enrollment.get_user')
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
            self.base._get_enrollment_data(data, course_settings),  # pylint: disable=protected-access
            expected_data,
        )

        del course_settings['external_enrollment_mode_override']
        expected_data['mode'] = data['course_mode']

        self.assertEqual(
            self.base._get_enrollment_data(data, course_settings),  # pylint: disable=protected-access
            expected_data,
        )

        data['is_active'] = False
        expected_data['is_active'] = False

        self.assertEqual(
            self.base._get_enrollment_data(data, course_settings),  # pylint: disable=protected-access
            expected_data,
        )

        expected_data['mode'] = None
        expected_data['is_active'] = True
        expected_data['course_details']['course_id'] = None

        self.assertEqual(
            self.base._get_enrollment_data({}, {}),  # pylint: disable=protected-access
            expected_data,
        )

    def test_get_enrollment_headers(self):
        """Testing _get_enrollment_headers method."""
        expected_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Edx-Api-Key": settings.EDX_API_KEY,
        }

        self.assertEqual(self.base._get_enrollment_headers(), expected_headers)  # pylint: disable=protected-access

    def test_get_enrollment_url(self):
        """Testing _get_enrollment_url method."""
        expected_url = 'https://edx-external-instance.com/api/v0/enrollments'
        course_settings = {
            'external_enrollment_api_url': expected_url,
        }
        self.assertIsNone(
            self.base._get_enrollment_url(course_settings={}),  # pylint: disable=protected-access
        )
        self.assertEqual(
            expected_url,
            self.base._get_enrollment_url(course_settings),  # pylint: disable=protected-access
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
