""" Backend abstraction """
from importlib import import_module
from django.conf import settings


def get_staff_or_owner(*args, **kwargs):  # pylint: disable=unused-argument
    """ Get IsStaffOrOwner Class """

    backend_function = settings.OEE_OPENEDX_PERMISSIONS
    backend = import_module(backend_function)

    return backend.IsStaffOrOwner


def get_api_key_permission(*args, **kwargs):  # pylint: disable=unused-argument
    """ Get ApiKeyHeaderPermissionIsAuthenticated Class """

    backend_function = settings.OEE_OPENEDX_PERMISSIONS
    backend = import_module(backend_function)

    return backend.ApiKeyHeaderPermissionIsAuthenticated
