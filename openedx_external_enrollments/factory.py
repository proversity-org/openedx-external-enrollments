"""Openedx external enrollments factory file."""
from openedx_external_enrollments.external_enrollments.edx_enterprise_external_enrollment import (
    EdxEnterpriseExternalEnrollment,
)
from openedx_external_enrollments.external_enrollments.edx_instance_external_enrollment import (
    EdxInstanceExternalEnrollment,
)


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
