"""Site Configurations definitions."""
from importlib import import_module

from django.conf import settings


def get_configuration_helpers(*args, **kwargs):
    """ Get configuration_helpers function."""
    backend_function = settings.OEE_SITE_CONFIGURATION_BACKEND
    backend = import_module(backend_function)
    return backend.get_configuration_helpers(*args, **kwargs)


configuration_helpers = get_configuration_helpers()
