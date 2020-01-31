"""
Common utilities for the course experience, including course outline.
"""
from completion.models import BlockCompletion

from django.contrib.auth.models import User
from lms.djangoapps.course_api.blocks.api import get_blocks
from lms.djangoapps.course_blocks.utils import get_student_module_as_dict
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.request_cache.middleware import request_cached
from xmodule.modulestore.django import modulestore


@request_cached
def get_course_outline_block_tree(request, course_id, user=None, all_users=False):
    """
    Returns the root block of the course outline, with children as blocks.
    """

    def populate_children(block, all_blocks):
        """
        Replace each child id with the full block for the child.

        Given a block, replaces each id in its children array with the full
        representation of that child, which will be looked up by id in the
        passed all_blocks dict. Recursively do the same replacement for children
        of those children.
        """
        children = block.get('children', [])

        for i in range(len(children)):
            child_id = block['children'][i]
            child_detail = populate_children(all_blocks[child_id], all_blocks)
            block['children'][i] = child_detail

        return block

    def set_last_accessed_default(block, all_users=False):
        """
        Set default of False for resume_block on all blocks.
        """
        block['resume_block'] = False
        if all_users:
            block['completion'] = {}
        else:
            block['complete'] = False
            block['completion_date'] = None
        for child in block.get('children', []):
            set_last_accessed_default(child, all_users=all_users)

    def mark_blocks_completed(block, user, course_key):
        """
        Walk course tree, marking block completion.
        Mark 'most recent completed block as 'resume_block'

        """
        last_completed_child_position = BlockCompletion.get_latest_block_completed(user, course_key)

        if last_completed_child_position:
            completion_iterable = BlockCompletion.user_course_completion_queryset(user, course_key)
            course_block_completions = {completion.full_block_key: completion for completion in completion_iterable}

            # Mutex w/ NOT 'course_block_completions'
            recurse_mark_complete(
                course_block_completions=course_block_completions,
                latest_completion=last_completed_child_position,
                block=block
            )

    def mark_blocks_completed_all_students(block, course_key):
        enrolled_students = User.objects.filter(
            courseenrollment__course_id=course_key,
            courseenrollment__is_active=1
        ).order_by('username')
        user_ids = [u.id for u in enrolled_students]
        block['users_info'] = {u.id: {'email': u.email, 'username': u.username} for u in enrolled_students}

        completions = BlockCompletion.objects.filter(user_id__in=user_ids, course_key=course_key)
        for u in enrolled_students:
            course_block_completions = {completion.full_block_key: completion
                                        for completion in completions
                                        if completion.user_id == u.id}

            recurse_mark_complete_for_user(
                course_block_completions=course_block_completions,
                block=block,
                user_id=u.id
            )

    def recurse_mark_complete(course_block_completions, latest_completion, block):
        """
        Helper function to walk course tree dict,
        marking blocks as 'complete' and 'last_complete'

        If all blocks are complete, mark parent block complete
        mark parent blocks of 'last_complete' as 'last_complete'

        :param course_block_completions: dict[course_completion_object] =  completion_value
        :param latest_completion: course_completion_object
        :param block: course_outline_root_block block object or child block

        :return:
            block: course_outline_root_block block object or child block
        """
        block_key = block.serializer.instance

        compl = course_block_completions.get(block_key)
        if compl and compl.completion:
            block['complete'] = True
            block['completion_date'] = compl.modified
            if block_key == latest_completion.full_block_key:
                block['resume_block'] = True

        if block.get('children'):
            for idx in range(len(block['children'])):
                recurse_mark_complete(
                    course_block_completions,
                    latest_completion,
                    block=block['children'][idx]
                )
                if block['children'][idx]['resume_block'] is True:
                    block['resume_block'] = True

            completable_blocks = [child for child in block['children'] if child['type'] != 'discussion']
            completed_blocks = [child for child in completable_blocks if child['complete']]

            if len(completed_blocks) == len(completable_blocks):
                block['complete'] = True
                block['completion_date'] = get_max_completion_date(completed_blocks)

    def recurse_mark_complete_for_user(course_block_completions, block, user_id):
        block_key = block.serializer.instance

        compl = course_block_completions.get(block_key)
        if 'completion' not in block:
            block['completion'] = {}
        if user_id not in block['completion']:
            block['completion'][user_id] = {
                'complete': False,
                'completion_date': None
            }
        if compl and compl.completion:
            block['completion'][user_id]['complete'] = True
            block['completion'][user_id]['completion_date'] = compl.modified

        if block.get('children'):
            for idx in range(len(block['children'])):
                recurse_mark_complete_for_user(
                    course_block_completions,
                    block=block['children'][idx],
                    user_id=user_id
                )

            completable_blocks = [child for child in block['children'] if child['type'] != 'discussion']
            completed_blocks = [child for child in completable_blocks
                                if child.get('completion', {}).get(user_id, {}).get('complete')]

            if len(completed_blocks) == len(completable_blocks):
                block['completion'][user_id]['complete'] = True
                block['completion'][user_id]['completion_date'] = get_max_completion_date(completed_blocks, user_id)

    def get_max_completion_date(items, user_id=None):
        if user_id:
            arr = []
            for item in items:
                tmp = item.get('completion', {}).get(user_id, {}).get('completion_date')
                if tmp is not None:
                    arr.append(tmp)
        else:
            arr = [item['completion_date'] for item in items if item['completion_date'] is not None]
        if arr:
            return max(arr)
        else:
            return None

    def mark_last_accessed(user, course_key, block):
        """
        Recursively marks the branch to the last accessed block.
        """
        block_key = block.serializer.instance
        student_module_dict = get_student_module_as_dict(user, course_key, block_key)

        last_accessed_child_position = student_module_dict.get('position')
        if last_accessed_child_position and block.get('children'):
            block['resume_block'] = True
            if last_accessed_child_position <= len(block['children']):
                last_accessed_child_block = block['children'][last_accessed_child_position - 1]
                last_accessed_child_block['resume_block'] = True
                mark_last_accessed(user, course_key, last_accessed_child_block)
            else:
                # We should be using an id in place of position for last accessed.
                # However, while using position, if the child block is no longer accessible
                # we'll use the last child.
                block['children'][-1]['resume_block'] = True

    course_key = CourseKey.from_string(course_id)
    course_usage_key = modulestore().make_course_usage_key(course_key)

    requested_user = user if user else request.user

    # Deeper query for course tree traversing/marking complete
    # and last completed block
    block_types_filter = [
        'course',
        'chapter',
        'sequential',
        'vertical',
        'html',
        'problem',
        'video',
        'discussion',
        'drag-and-drop-v2',
        'poll',
        'word_cloud',
        'openassessment'
    ]
    all_blocks = get_blocks(
        request,
        course_usage_key,
        user=requested_user,
        nav_depth=3,
        requested_fields=[
            'children',
            'display_name',
            'type',
            'due',
            'graded',
            'special_exam_info',
            'show_gated_sections',
            'format'
        ],
        block_types_filter=block_types_filter
    )

    course_outline_root_block = all_blocks['blocks'].get(all_blocks['root'], None)
    if course_outline_root_block:
        populate_children(course_outline_root_block, all_blocks['blocks'])
        set_last_accessed_default(course_outline_root_block, all_users)

        if all_users:
            mark_blocks_completed_all_students(
                block=course_outline_root_block,
                course_key=course_key
            )
        else:
            mark_blocks_completed(
                block=course_outline_root_block,
                user=requested_user,
                course_key=course_key
            )
    return course_outline_root_block


def get_resume_block(block):
    """
    Gets the deepest block marked as 'resume_block'.

    """
    if not block['resume_block']:
        return None
    if not block.get('children'):
        return block

    for child in block['children']:
        resume_block = get_resume_block(child)
        if resume_block:
            return resume_block
    return block
