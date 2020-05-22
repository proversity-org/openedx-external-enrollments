"""Courseware definitions."""

from importlib import import_module
from django.conf import settings


def get_user(*args, **kwargs):
    """ Return get_user result method."""
    backend_function = settings.OEE_STUDENT_BACKEND
    backend = import_module(backend_function)

    return backend.get_user_backend(*args, **kwargs)


def get_course_enrollment():
    """ Return CourseEnrollment model."""
    backend_function = settings.OEE_STUDENT_BACKEND
    backend = import_module(backend_function)

    return backend.get_course_enrollment_backend()


CourseEnrollment = get_course_enrollment()
