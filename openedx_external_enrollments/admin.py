"""
Django admin page
"""
from django.contrib import admin

from openedx_external_enrollments.models import (
    EnrollmentRequestLog,
    ProgramSalesforceEnrollment,
)


class ProgramSalesforceEnrollmentAdmin(admin.ModelAdmin):
    """
    Program salesforce enrollment model admin.
    """
    list_display = [
        'bundle_id',
    ]

    search_fields = ('bundle_id', 'meta',)


class EnrollmentRequestLogAdmin(admin.ModelAdmin):
    """
    Enrollment request model admin.
    """
    list_display = [
        'request_type',
        'created_at',
        'updated_at',
    ]

    search_fields = ('request_type', 'details',)


admin.site.register(EnrollmentRequestLog, EnrollmentRequestLogAdmin)
admin.site.register(ProgramSalesforceEnrollment, ProgramSalesforceEnrollmentAdmin)
