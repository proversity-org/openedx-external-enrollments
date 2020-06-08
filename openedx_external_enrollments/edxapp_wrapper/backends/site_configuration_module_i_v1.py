"""Site Configuration backend file."""
from openedx.core.djangoapps.site_configuration import helpers  # pylint: disable=import-error


def get_configuration_helpers():
    """Backend function."""
    return helpers
