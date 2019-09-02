""" Course home backend abstraction """
from importlib import import_module
from django.conf import settings

def calculate_course_home(*args, **kwargs):
    """ Backend function to calculate course home """

    backend_module = settings.OEE_COURSE_HOME_MODULE
    backend = import_module(backend_module)

    return backend.calculate_course_home(*args, **kwargs)