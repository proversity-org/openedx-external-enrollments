"""Tests factory file."""
from django.test import TestCase

from openedx_external_enrollments.external_enrollments.edx_enterprise_external_enrollment import (
    EdxEnterpriseExternalEnrollment,
)
from openedx_external_enrollments.external_enrollments.edx_instance_external_enrollment import (
    EdxInstanceExternalEnrollment,
)
from openedx_external_enrollments.factory import ExternalEnrollmentFactory


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
