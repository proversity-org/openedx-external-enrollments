"""
Model module
"""
from django.db import models
from jsonfield.fields import JSONField


class ProgramSalesforceEnrollment(models.Model):
    """
    Model to persist salesforce enrollment course / program configurations.
    """

    bundle_id = models.CharField(max_length=48, unique=True)
    meta = JSONField(null=False, blank=True)

    class Meta(object):
        """
        Model meta class.
        """
        app_label = "openedx_external_enrollments"

    def __unicode__(self):
        return self.bundle_id


class EnrollmentRequestLog(models.Model):
    """
    Model to persist enrollment requests
    """

    request_type = models.CharField(max_length=10)
    details = JSONField(null=False, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(object):
        """
        Model meta class.
        """
        app_label = "openedx_external_enrollments"
