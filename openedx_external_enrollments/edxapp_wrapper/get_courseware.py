"""Courseware definitions."""

from importlib import import_module

from django.conf import settings


def get_course_by_id(*args, **kwargs):
    """ Return get_course_by_id method."""
    backend_function = settings.OEE_COURSEWARE_BACKEND
    backend = import_module(backend_function)

    return backend.get_course_by_id_backend(*args, **kwargs)
