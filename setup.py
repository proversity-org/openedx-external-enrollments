"""
Setup file for openedx_external_enrollments Django plugin.
"""

from __future__ import print_function

import os
import re

from setuptools import setup


def get_version(*file_paths):
    """
    Extract the version string from the file at the given relative path fragments.
    """
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename).read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


VERSION = get_version('openedx_external_enrollments', '__init__.py')


setup(
    name='openedx-external-enrollments',
    version=VERSION,
    description='External Enrollments',
    author='eduNEXT',
    author_email='contact@edunext.co',
    packages=[
        'openedx_external_enrollments'
    ],
    include_package_data=True,
    install_requires=[],
    zip_safe=False,
    entry_points={
        "lms.djangoapp": [
            'openedx_external_enrollments = openedx_external_enrollments.apps:OpenedxExternalEnrollmentConfig',
        ],
    }
)
