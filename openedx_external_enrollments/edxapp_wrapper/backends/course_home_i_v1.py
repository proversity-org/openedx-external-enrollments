"""
Course home concrete module
"""
import datetime

from courseware.courses import get_course_by_id
from student.models import CourseEnrollment

from opaque_keys.edx.keys import CourseKey
import pytz


def calculate_course_home(course_id, user):

    course_key = CourseKey.from_string(course_id)
    course = get_course_by_id(course_key)
    user_is_enrolled = CourseEnrollment.is_enrolled(user, course_key)

    if is_external_course(course_id) and user_is_enrolled:
        custom_course_settings = course.other_course_settings
        course_entry_points = custom_course_settings.get("course_entry_points", [])
        enrollment = CourseEnrollment.get_enrollment(user, course_key)

        if course_entry_points:
            if course.self_paced:
                dates_to_check = [enrollment.created, course.start]
                student_start = max(dates_to_check)
            else:
                student_start = course.start

            difference = datetime.datetime.utcnow().replace(tzinfo=pytz.utc) - student_start
            days_since_course_start = difference.days
            first_step = course_entry_points[0]
            valid_from_week = first_step.get("valid_from_week",0)
            valid_through_week = first_step.get("valid_through_week", 0)

            if first_step and days_since_course_start <= (valid_through_week - valid_from_week +1) * 7:
                url = "/courses/{}/jump_to_id/{}".format(course_id, first_step.get("location_id"))
                return url
        return custom_course_settings.get("external_course_target")

    return None

def is_external_course(course_id):
    """
    Decide if the course was confiured as external or not
    """
    course_key = CourseKey.from_string(course_id)
    course = get_course_by_id(course_key)
    custom_course_settings = course.other_course_settings

    return (
        custom_course_settings.get("external_course_run_id") and
        custom_course_settings.get("external_course_target")
    )
