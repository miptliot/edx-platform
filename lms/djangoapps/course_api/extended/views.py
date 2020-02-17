import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.lib.api.course_exists import check_course_exists, check_staff_permission
from openedx.features.course_experience.utils import get_course_outline_block_tree
from util.json_request import JsonResponse

from lms.djangoapps.course_api.blocks.api import get_blocks
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from courseware.user_state_client import DjangoXBlockUserStateClient
from course_shifts.models import CourseShiftUser
from course_shifts.utils import course_shifts_enabled
from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore

from openassessment.assessment.api.peer import PEER_TYPE
from openassessment.assessment.models import Assessment
from openassessment.assessment.models.peer import AssessmentFeedback
from openassessment.workflow.models import AssessmentWorkflow
from submissions.models import Submission, Score
from student.models import AnonymousUserId


@check_course_exists(check_staff_permission=True)
def course_completion(request, course):
    all_users = request.GET.get('all_users') == '1'

    if not all_users:
        user, response = _get_user(request)
        if not user:
            return response
    else:
        user = User.objects.filter(is_superuser=True).first()

    blocks = get_course_outline_block_tree(request, str(course.id), user, all_users)
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
                'format': section.format,
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


@check_course_exists(check_staff_permission=True)
def ora_studets_progress(request, course):
    openassessment_blocks = modulestore().get_items(course.id, qualifiers={'category': 'openassessment'})
    assessment_workflow_data = AssessmentWorkflow.objects.filter(course_id=str(course.id))\
            .exclude(status__in=['cancelled'])

    submissions_uuid_list = []
    submissions_uuid_short_list = []
    student_ids_dict = {}  # { anonymous_user_id: { username: ... , email: ... } }
    submissions_dict = {}  # { submission_uuid: anonymous_user_id }
    feedback_dict = {}     # { submission_uuid: feedback_text }
    submission_uuid_to_block = {}  # { submission_uuid: block_id }
    submissions_id_to_uuid = {}
    submissions_uuid_to_score = {}

    for item in assessment_workflow_data:
        submission_uuid_to_block[item.submission_uuid] = item.item_id
        submissions_uuid_short_list.append(item.submission_uuid.replace('-', ''))
        submissions_uuid_list.append(item.submission_uuid)
        if item.submission_uuid not in feedback_dict:
            feedback_dict[item.submission_uuid] = None

    submissions = Submission.objects.filter(uuid__in=submissions_uuid_short_list).select_related('student_item')
    for s in submissions:
        uuid_str = str(uuid.UUID(str(s.uuid)))
        if s.student_item.student_id not in student_ids_dict:
            student_ids_dict[s.student_item.student_id] = {}
        if uuid_str not in submissions_dict:
            submissions_dict[uuid_str] = s.student_item.student_id
        if uuid_str not in submissions_id_to_uuid:
            submissions_id_to_uuid[s.id] = uuid_str

    scores = Score.objects.filter(submission_id__in=submissions_id_to_uuid.keys()).order_by('created_at')\
            .select_related('submission')
    for score in scores:
        submissions_uuid_to_score[submissions_id_to_uuid[score.submission.id]] = score

    feedback_data = AssessmentFeedback.objects.filter(submission_uuid__in=feedback_dict.keys())
    for feedback_item in feedback_data:
        feedback_dict[str(feedback_item.submission_uuid)] = feedback_item.feedback_text

    users = AnonymousUserId.objects.filter(course_id=course.id).select_related('user')
    for u in users:
        student_ids_dict[u.anonymous_user_id] = {
            'username': u.user.username,
            'email': u.user.email,
            'user_id': u.user.id,
            'first_name': u.user.first_name,
            'last_name': u.user.last_name,
            'anonymous_user_id': u.anonymous_user_id
        }

    peer_assessments_dict = {}
    peer_assessments = Assessment.objects.filter(submission_uuid__in=submissions_uuid_list, score_type=PEER_TYPE)\
        .prefetch_related('parts').prefetch_related('parts__criterion').prefetch_related('parts__option')
    for peer_item in peer_assessments:
        block_id = submission_uuid_to_block[peer_item.submission_uuid]
        if block_id not in peer_assessments_dict:
            peer_assessments_dict[block_id] = {
                'submissions': {},
                'users': {}
            }
        if peer_item.submission_uuid not in peer_assessments_dict[block_id]['submissions']:
            peer_assessments_dict[block_id]['submissions'][peer_item.submission_uuid] = []
        if peer_item.scorer_id not in peer_assessments_dict[block_id]['users']:
            peer_assessments_dict[block_id]['users'][peer_item.scorer_id] = []
        criterions = []
        for part in peer_item.parts.all():
            criterions.append({
                'feedback': part.feedback,
                'criterion': part.criterion.label,
                'result': part.option.label,
                'points': part.option.points
            })

        peer_assessments_dict[block_id]['submissions'][peer_item.submission_uuid].append({
            'scorer_id': peer_item.scorer_id,
            'feedback': peer_item.feedback,
            'criterions': criterions,
            'scorer': student_ids_dict[peer_item.scorer_id],
        })

        peer_assessments_dict[block_id]['users'][peer_item.scorer_id].append({
            'student': student_ids_dict[submissions_dict[peer_item.submission_uuid]],
            'feedback': peer_item.feedback,
            'criterions': criterions
        })

    result = []
    for ora_block in openassessment_blocks:
        users_lst = []
        for item in assessment_workflow_data:
            if item.item_id == str(ora_block.location):
                submission_uuid = str(item.submission_uuid)
                student_info = student_ids_dict[submissions_dict[submission_uuid]].copy()
                student_info.update({
                    'created': str(item.created),
                    'modified': str(item.modified),
                    'status': str(item.status),
                    'feedback_text': feedback_dict[submission_uuid],
                    'score': 0,
                    'score_text': None,
                    'responses_from_other': [],
                    'my_responses': []
                })
                if submission_uuid in submissions_uuid_to_score:
                    score = submissions_uuid_to_score[submission_uuid]
                    student_info['score'] = score.to_float()
                    student_info['score_text'] = str(score.points_earned) + '/' + str(score.points_possible)
                if item.item_id in peer_assessments_dict:
                    student_info['responses_from_other'] = peer_assessments_dict[item.item_id]['submissions']\
                        .get(submission_uuid, [])
                    student_info['my_responses'] = peer_assessments_dict[item.item_id]['users']\
                        .get(student_info['anonymous_user_id'], [])
                users_lst.append(student_info)

        result.append({
            'id': str(ora_block.location),
            'display_name': ora_block.display_name,
            'rubric_criteria': ora_block.rubric_criteria,
            'users': users_lst
        })

    return JsonResponse(sorted(result, key=lambda k: k['display_name']))


@check_course_exists(check_staff_permission=True)
def course_enrollments(request, course):
    enrollments = CourseEnrollment.objects.filter(course_id=course.id, is_active=1).select_related('user')
    course_shifts_users_dict = {}
    if course_shifts_enabled(course):
        course_shifts_users = CourseShiftUser.objects.filter(course_key=course.id).select_related('course_shift')
        for csu in course_shifts_users:
            course_shifts_users_dict[csu.user_id] = csu.course_shift.to_dict()

    result = []
    for enrollment in enrollments:
        result.append({
            'user_id': enrollment.user.id,
            'username': enrollment.user.username,
            'email': enrollment.user.email,
            'first_name': enrollment.user.first_name,
            'last_name': enrollment.user.last_name,
            'mode': enrollment.mode,
            'created': str(enrollment.created),
            'course_shift': course_shifts_users_dict.get(enrollment.user.id)
        })

    return JsonResponse({
        "success": True,
        "error": None,
        "data": result
    })


@check_staff_permission
def user_enrollments(request):
    user, response = _get_user(request)
    if not user:
        return response

    result = []
    enrollments = CourseEnrollment.enrollments_for_user_with_overviews_preload(user)
    for enrollment in enrollments:
        course_overview = enrollment.course_overview
        if course_overview:
            lms_url = configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL)
            course_url = lms_url + reverse('openedx.course_experience.course_home',
                                           kwargs={'course_id': str(course_overview.id)})
            result.append({
                'course_id': str(course_overview.id),
                'course_url': course_url,
                'display_name': course_overview.display_name,
                'org': course_overview.org,
                'mode': enrollment.mode
            })

    return JsonResponse({
        "success": True,
        "error": None,
        "data": result
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
