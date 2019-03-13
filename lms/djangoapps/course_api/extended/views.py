from django.contrib.auth.models import User
from openedx.core.lib.api.course_exists import check_course_exists
from openedx.features.course_experience.utils import get_course_outline_block_tree
from util.json_request import JsonResponse

from lms.djangoapps.course_api.blocks.api import get_blocks
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from courseware.user_state_client import DjangoXBlockUserStateClient


@check_course_exists(check_staff_permission=True)
def course_completion(request, course):
    user, response = _get_user(request)
    if not user:
        return response

    blocks = get_course_outline_block_tree(request, str(course.id), user)
    return JsonResponse({
        "success": True,
        "error": None,
        "blocks": blocks
    })


@check_course_exists(check_staff_permission=True)
def course_progress(request, course):
    user, response = _get_user(request)
    if not user:
        return response

    result = []

    blocks_data = get_blocks(request, course.location, user,
                             requested_fields=['display_name', 'type'])
    blocks = blocks_data.get('blocks', {})

    user_state_client = DjangoXBlockUserStateClient(user)
    user_state_dict = user_state_client.get_all_blocks(user, course.id)

    course_grade = CourseGradeFactory().read(user, course)
    courseware_summary = course_grade.chapter_grades
    for chapter_key, chapter in courseware_summary.items():
        res_chapter = {
            'id': str(chapter_key),
            'type': 'chapter',
            'display_name': chapter['display_name'],
            'sections': []
        }
        res_sections = []
        for section in chapter['sections']:
            earned = section.all_total.earned
            total = section.all_total.possible
            res_problems = []
            for key, score in section.problem_scores.items():
                key_loc = str(key)
                if score.first_attempted:
                    last_answer_date = user_state_dict.get(key_loc).updated if key_loc in user_state_dict else None
                else:
                    last_answer_date = None
                res_problems.append({
                    'display_name': blocks[key_loc]['display_name'] if key_loc in blocks else '',
                    'type': blocks[key_loc]['type'] if key_loc in blocks else '',
                    'possible': score.possible,
                    'earned': score.earned,
                    'score': _get_float_value((score.earned * 1.0) / score.possible) if score.possible > 0 else 0,
                    'last_answer_date': last_answer_date,
                    'id': key_loc
                })
            res_sections.append({
                'display_name': section.display_name,
                'score': _get_float_value(section.percent_graded) if earned > 0 and total > 0 else 0,
                'possible': total,
                'earned': earned,
                'due': section.due,
                'problems': res_problems,
                'graded': section.graded,
                'type': 'sequential',
                'id': str(section.location)
            })
        res_chapter['sections'] = res_sections
        result.append(res_chapter)
    return JsonResponse({
        "success": True,
        "error": None,
        "data": result,
        "total_grade": _get_float_value(course_grade.percent)
    })


def _get_float_value(val):
    return float(format(val, '.2f'))


def _get_user(request):
    kwargs = {}
    username = request.GET.get('username')
    if username:
        kwargs['username'] = username.strip()

    email = request.GET.get('email')
    if email:
        kwargs['email'] = email.strip()

    user_id = request.GET.get('user_id')
    if user_id:
        try:
            kwargs['id'] = int(user_id)
        except ValueError:
            pass

    if kwargs:
        try:
            user = User.objects.get(**kwargs)
        except User.DoesNotExist:
            return None, JsonResponse({
                "success": False,
                "error": "User not found"
            })
        except User.MultipleObjectsReturned:
            return None, JsonResponse({
                "success": False,
                "error": "More than one user was found"
            })
    else:
        user = request.user
        if not user.is_authenticated:
            return None, JsonResponse({
                "success": False,
                "error": "Please pass 'username', 'email' or 'user_id' param"
            })
    return user, None
