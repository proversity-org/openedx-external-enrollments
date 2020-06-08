"""External enrollments method file."""
import logging

from openedx_external_enrollments.edxapp_wrapper.get_site_configuration import configuration_helpers
from openedx_external_enrollments.factory import ExternalEnrollmentFactory

LOG = logging.getLogger(__name__)


def execute_external_enrollment(data, course):
    """
    Execute an enrollment for the given data and course.

    Args:
        data: dict with the enrollment data.
        course: instance of CourseDescriptor.
    """
    try:
        controller = course.other_course_settings.get('external_platform_target', '')
    except AttributeError:
        LOG.error('Course [%s] not configured as external.', str(course.id))
        return

    valid_external_targets = configuration_helpers.get_value('VALID_EXTERNAL_TARGETS', [])

    if controller.lower() not in valid_external_targets:
        LOG.warning(
            'The controller %s is not present in the valid external targets list %s.',
            controller,
            valid_external_targets,
        )
        return

    enrollment_controller = ExternalEnrollmentFactory.get_enrollment_controller(
        controller=controller,
    )

    enrollment_controller._post_enrollment(data, course.other_course_settings)  # pylint: disable=protected-access
