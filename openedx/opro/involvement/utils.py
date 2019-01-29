import datetime
import jwt
import time
from courseware.courses import get_course_by_id
from opaque_keys.edx.keys import CourseKey
from django.conf import settings
from django.utils import timezone

from .models import UserCourseInvolvement, InvolvementLink
from xmodule.course_module import INVOLVEMENT_OPTIONAL, INVOLVEMENT_REQUIRED


EXAMUS_INVOLVEMENT_ENABLED = getattr(settings, 'EXAMUS_INVOLVEMENT_ENABLED', False)
EXAMUS_INVOLVEMENT_TOKEN_NAME = getattr(settings, 'EXAMUS_INVOLVEMENT_TOKEN_NAME', '')
EXAMUS_INVOLVEMENT_TOKEN_SECRET = getattr(settings, 'EXAMUS_INVOLVEMENT_TOKEN_SECRET', '')
EXAMUS_INVOLVEMENT_API_HOST = getattr(settings, 'EXAMUS_INVOLVEMENT_API_HOST', '')
EXAMUS_INVOLVEMENT_CHARTS_HOST = getattr(settings, 'EXAMUS_INVOLVEMENT_CHARTS_HOST', '')
EXAMUS_INVOLVEMENT_BLOCK_TYPE = getattr(settings, 'EXAMUS_INVOLVEMENT_BLOCK_TYPE', 'sequential')

JWT_ALGORITHM = 'HS256'
JWT_TOKEN_LIFETIME = 24 * 60 * 60


def involvement_settings_active():
    return bool(EXAMUS_INVOLVEMENT_ENABLED)


def involvement_is_enabled(course):
    settings_active = involvement_settings_active()
    if settings_active:
        return course.involvement in (INVOLVEMENT_OPTIONAL, INVOLVEMENT_REQUIRED)
    return False


def involvement_block_type():
    return EXAMUS_INVOLVEMENT_BLOCK_TYPE


def get_user_involvement(course_key, user):
    user_allow_involvement = False
    involvement = None
    try:
        involvement = UserCourseInvolvement.objects.get(course_key=course_key, user=user)
        user_allow_involvement = involvement.is_active
    except UserCourseInvolvement.DoesNotExist:
        pass
    return involvement, user_allow_involvement


def get_blocks_involvement(course_key, user):
    result = {}
    links = InvolvementLink.objects.filter(course_key=course_key, user=user)
    for link in links:
        token = prepare_jwt_token({
            'access': 'r',
            'link_id': link.link_id
        })
        result[str(link.usage_key)] = {
            'url': '%s/graphics/dev/graphics.html?token=%s' % (
                EXAMUS_INVOLVEMENT_CHARTS_HOST, token
            ),
            'block_type': link.block_type,
            'link_id': link.link_id
        }
    return result


def ask_enable_involvement(course, user):
    if not involvement_settings_active():
        return False

    if isinstance(course, (str, unicode)):
        course_key = CourseKey.from_string(course)
        course = get_course_by_id(course_key)
    else:
        course_key = course.id

    if not involvement_is_enabled(course):
        return False

    if course.involvement in (INVOLVEMENT_OPTIONAL, INVOLVEMENT_REQUIRED):
        involvement, involvement_allowed = get_user_involvement(course_key, user)

        if not involvement_allowed:
            ask_enable = False
            if course.involvement == INVOLVEMENT_REQUIRED:
                ask_enable = True
            elif course.involvement == INVOLVEMENT_OPTIONAL:
                if involvement:
                    dt_now = timezone.now()
                    dt_day_ago = dt_now - datetime.timedelta(days=1)
                    if involvement.last_action_time < dt_day_ago:
                        ask_enable = True
                else:
                    ask_enable = True
            return ask_enable
    return False


def prepare_jwt_token(payload):
    payload['name'] = EXAMUS_INVOLVEMENT_TOKEN_NAME
    payload['exp'] = int(time.time()) + JWT_TOKEN_LIFETIME
    print 'jwt.encode(', payload, ',', EXAMUS_INVOLVEMENT_TOKEN_SECRET, ',', JWT_ALGORITHM, ')'
    return jwt.encode(payload, EXAMUS_INVOLVEMENT_TOKEN_SECRET, JWT_ALGORITHM)
