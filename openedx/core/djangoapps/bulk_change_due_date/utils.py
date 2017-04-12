import dateutil
from django.contrib.auth.models import User
from django.utils.timezone import utc
from django.utils.translation import ugettext as _
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey
from openedx.core.djangoapps.course_groups.cohorts import get_cohort_by_name
from .core import UserProblemSetDate, UserProblemAddDays, UserCourseSetDate, \
    UserCourseAddDays, CohortProblemSetDate, CohortProblemAddDays, CohortCourseSetDate, CohortCourseAddDays


def are_change_due_keys_broken(keys, course_key):
    if len(keys) != 3:
        return "Need 3 keys, got {}: {}".format(len(keys), ",".join(x for x in keys.keys()))
    if 'user' in keys:
        try:
            user = User.objects.get(username=keys['user'])
        except ValueError:
            return _("No such user: {}").format(keys['user'])
    if 'cohort' in keys:
        try:
            cohort = get_cohort_by_name(course_key, keys['cohort'])
        except ValueError:
            return _("No such cohort: {}").format(keys['cohort'])
    if 'block_key' in keys:
        try:
            block = UsageKey.from_string(keys['block_key'])
        except InvalidKeyError:
            return _("No such block: {}").format(keys['block_key'])
    if 'add_days' in keys:
        try:
            add_days = int(keys['add_days'])
        except ValueError:
            return _("Add days must be integer; {} - is not integer ").format(keys['add_days'])
    if 'set_date' in keys:
        try:
            set_date = dateutil.parser.parse(keys['set_date'], dayfirst=True).replace(tzinfo=utc)
        except ValueError:
            return _("Didn't understand date '{}'; Must be in dd/mm/yyyy").format(keys['set_date'])
    return 0


def choose_date_changer(keys):
    key_set = set(keys)
    if len(key_set) != 3:
        raise ValueError("Internal Error. Invalid number of keys ({}), need 3. Keys:{}".format(len(keys), str(keys)))

    user_problem_set_date_keys = ['user', 'set_date', 'block_key']
    if all(x in key_set for x in user_problem_set_date_keys):
        return UserProblemSetDate.wrap()

    user_problem_add_days_keys = ['user', 'add_days', 'block_key']
    if all(x in key_set for x in user_problem_add_days_keys):
        return UserProblemAddDays.wrap()

    user_course_set_date_keys = ['user', 'set_date', 'course_key']
    if all(x in key_set for x in user_course_set_date_keys):
        return UserCourseSetDate.wrap()

    user_course_add_days_keys = ['user', 'add_days', 'course_key']
    if all(x in key_set for x in user_course_add_days_keys):
        return UserCourseAddDays.wrap()

    cohort_problem_set_date_keys = ['cohort', 'set_date', 'block_key']
    if all(x in key_set for x in cohort_problem_set_date_keys):
        return CohortProblemSetDate.wrap()

    cohort_problem_add_days_keys = ['cohort', 'add_days', 'block_key']
    if all(x in key_set for x in cohort_problem_add_days_keys):
        return CohortProblemAddDays.wrap()

    cohort_course_set_date_keys = ['cohort', 'set_date', 'course_key']
    if all(x in key_set for x in cohort_course_set_date_keys):
        return CohortCourseSetDate.wrap()

    cohort_course_add_days_keys = ['cohort', 'add_days', 'course_key']
    if all(x in key_set for x in cohort_course_add_days_keys):
        return CohortCourseAddDays.wrap()

    raise NotImplementedError("Keys combination not recognized. Keys: {}".format(str(keys)))
