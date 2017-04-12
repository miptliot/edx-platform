import logging
from functools import partial
from django.conf import settings
from django.utils.translation import ugettext_noop
from celery import task
from instructor_task.api_helper import submit_task

from instructor_task.tasks_helper import (
    run_main_task,
    BaseInstructorTask,
)
from .utils import choose_date_changer

"""
Pipeline: view -> submit_change_due_task -> external::submit_task -> change_due_dates -> external::run_main_task -> change_due_dates_task
"""

TASK_LOG = logging.getLogger('edx.celery.task')

# define value to use when no task_id is provided:
UNKNOWN_TASK_ID = 'unknown-task_id'
FILTERED_OUT_ROLES = ['staff', 'instructor', 'finance_admin', 'sales_admin']
# define values for update functions to use to return status to perform_module_state_update
UPDATE_STATUS_SUCCEEDED = 'succeeded'
UPDATE_STATUS_FAILED = 'failed'
UPDATE_STATUS_SKIPPED = 'skipped'


def submit_change_due_task(request, course_key, changedue_params):
    """
    Submits task to change due dates for user(s) for item(s)
    changedue_params: OrderedDict with 3 key. Each key is supposed to be one from pair:
        "user"/"cohort": $name
        "course"/"block": $location
        "add_days"/"set_date": numeric str/date str (like  2017/01/31)

    lms/djangoapps/instructor_task/api.py
    """
    task_type = 'change_due_dates'
    task_class = change_due_dates
    task_input = {
        "keys": [x for x in changedue_params.keys()],
        "values": [x for x in changedue_params.values()],
    }
    task_key = ''
    return submit_task(request, task_type, task_class, course_key, task_input, task_key)


@task(base=BaseInstructorTask)  # pylint: disable=not-callable
def change_due_dates(entry_id, xmodule_instance_args):
    """
    Change courseware due dates according to the given args
    """
    action_name = ugettext_noop('due dates changed')
    task_fn = partial(change_due_dates_task, xmodule_instance_args)
    return run_main_task(entry_id, task_fn, action_name)


def change_due_dates_task(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
    """
    Task to change due dates for given user/cohort and course item
    """
    try:
        fmt = u'Task: {task_id}, InstructorTask ID: {entry_id}, Course: {course_id}, Input: {task_input}'
        task_info_string = fmt.format(
            task_id=_xmodule_instance_args.get('task_id') if _xmodule_instance_args is not None else None,
            entry_id=_entry_id,
            course_id=course_id,
            task_input=_task_input
        )
        TASK_LOG.info(u'%s, Task type: %s, Starting task execution', task_info_string, action_name)

        params_keys = _task_input["keys"]
        params_values = _task_input["values"]
        date_changer = choose_date_changer(params_keys)
        changer = date_changer(*params_values)

        changer.change_due()
        changer.logging()
        return UPDATE_STATUS_SUCCEEDED
    except:
        TASK_LOG.exception(u"Task (%s) failed", _get_task_id_from_xmodule_args(_xmodule_instance_args), exc_info=True)
        return UPDATE_STATUS_FAILED


def _get_task_id_from_xmodule_args(xmodule_instance_args):
    """Gets task_id from `xmodule_instance_args` dict, or returns default value if missing."""
    return xmodule_instance_args.get('task_id', UNKNOWN_TASK_ID) if xmodule_instance_args is not None else UNKNOWN_TASK_ID
