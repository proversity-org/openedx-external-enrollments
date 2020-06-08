"""Tests External enrollments file."""
import logging

from django.test import TestCase
from mock import Mock, patch
from testfixtures import LogCapture

from openedx_external_enrollments.external_enrollments import execute_external_enrollment

MODULE = 'openedx_external_enrollments.external_enrollments'


class ExecuteExternalEnrollmentTest(TestCase):
    """Test class for execute_external_enrollment method."""

    @patch('openedx_external_enrollments.external_enrollments.configuration_helpers')
    def test_execute_external_enrollment(self, configuration_helpers_mock):
        """Testing execute_external_enrollment method."""
        course = Mock()
        course.id = 'test-course-id'
        data = {'fake': 'data'}
        course.other_course_settings.get.return_value = 'edx'
        configuration_helpers_mock.get_value.return_value = ['openedx']

        with LogCapture(level=logging.WARNING) as log_capture:
            execute_external_enrollment(data, course)
            log = 'The controller {} is not present in the valid external targets list {}.'.format(
                'edx',
                ['openedx'],
            )
            log_capture.check(
                (MODULE, 'WARNING', log),
            )

        with patch('openedx_external_enrollments.external_enrollments.ExternalEnrollmentFactory') as factory_mock:
            controller_mock = Mock()
            course.other_course_settings.get.return_value = 'openedx'
            factory_mock.get_enrollment_controller.return_value = controller_mock

            execute_external_enrollment(data, course)

            controller_mock._post_enrollment.assert_called_once_with(  # pylint: disable=protected-access
                data,
                course.other_course_settings,
            )
            factory_mock.get_enrollment_controller.assert_called_once_with(
                controller='openedx',
            )

        course.other_course_settings.get.side_effect = AttributeError('test-exception')

        with LogCapture(level=logging.ERROR) as log_capture:
            execute_external_enrollment(data, course)
            log = 'Course [{}] not configured as external.'.format(course.id)
            log_capture.check(
                (MODULE, 'ERROR', log),
            )
