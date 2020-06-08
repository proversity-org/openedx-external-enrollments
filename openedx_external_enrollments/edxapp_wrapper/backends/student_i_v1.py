"""Student backend file."""

from student.models import CourseEnrollment, get_user  # pylint: disable=import-error


def get_user_backend(*args, **kwargs):
    """Return the method get_user from student.models."""
    return get_user(*args, **kwargs)


def get_course_enrollment_backend():
    """Return the model CourseEnrollment from the module student.models."""
    return CourseEnrollment
