"""Tests BaseExternalEnrollment class file."""
import logging

from django.test import TestCase
from mock import patch
from rest_framework import status
from testfixtures import LogCapture

from openedx_external_enrollments.external_enrollments.base_external_enrollment import BaseExternalEnrollment
from openedx_external_enrollments.models import EnrollmentRequestLog

module = 'openedx_external_enrollments.external_enrollments.base_external_enrollment'


class BaseExternalEnrollmentTest(TestCase):
    """Test class for BaseExternalEnrollment class."""

    def setUp(self):
        """Set test database."""
        self.base = BaseExternalEnrollment()
        self.base.__str__ = lambda: 'test-class'

    @patch('openedx_external_enrollments.external_enrollments.base_external_enrollment.requests.post')
    def test_execute_post(self, mock_post):
        """Testing _execute_post method."""
        url = 'test_url'
        data = 'data'
        headers = 'headers'
        json_data = 'json_data'

        self.base._execute_post(  # pylint: disable=protected-access
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
            response = self.base._post_enrollment(data, course_settings)  # pylint: disable=protected-access
            log4 = 'External enrollment response for [{}] -- {}'.format(self.base.__str__(), data)
            log_capture.check(
                (module, 'INFO', log1),
                (module, 'INFO', log2),
                (module, 'INFO', log3),
                (module, 'INFO', log4),
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

        request_log = EnrollmentRequestLog.objects.filter(  # pylint: disable=no-member
            request_type=str(self.base),
            details=log_details,
        )
        self.assertEqual(len(request_log), 1)

        headers_mock.side_effect = NotImplementedError('My test error')

        with LogCapture(level=logging.INFO) as log_capture:
            response = self.base._post_enrollment(data, course_settings)  # pylint: disable=protected-access
            log4 = 'Failed to complete enrollment. Reason: {}'.format('My test error')
            log_capture.check(
                (module, 'INFO', log1),
                (module, 'INFO', log2),
                (module, 'INFO', log3),
                (module, 'ERROR', log4),
            )

        log_details['response'] = {'error': log4}
        request_log = EnrollmentRequestLog.objects.filter(  # pylint: disable=no-member
            request_type=str(self.base),
            details=log_details,
        )
        self.assertEqual(len(request_log), 1)

    def test_get_enrollment_data(self):
        """Testing _get_enrollment_data method."""
        with self.assertRaises(NotImplementedError):
            self.base._get_enrollment_data({}, {})  # pylint: disable=protected-access

    def test_get_enrollment_headers(self):
        """Testing _get_enrollment_headers method."""
        self.assertRaises(NotImplementedError, self.base._get_enrollment_headers)  # pylint: disable=protected-access

    def test_get_enrollment_url(self):
        """Testing _get_enrollment_url method."""
        with self.assertRaises(NotImplementedError):
            self.base._get_enrollment_url({})  # pylint: disable=protected-access
