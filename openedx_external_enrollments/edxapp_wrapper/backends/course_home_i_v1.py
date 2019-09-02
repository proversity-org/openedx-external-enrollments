"""
Course home concrete module
"""
from courseware.courses import get_course_by_id

from opaque_keys.edx.keys import CourseKey


def calculate_course_home(course_id):
    if is_external_course(course_id):
        course_key = CourseKey.from_string(course_id)
        course = get_course_by_id(course_key)
        custom_course_settings = course.other_course_settings
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
