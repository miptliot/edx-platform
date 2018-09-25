from celery import task
from celery_utils.logged_task import LoggedTask
from celery_utils.persist_on_failure import PersistOnFailureTask


class _BaseTask(PersistOnFailureTask, LoggedTask):  # pylint: disable=abstract-method
    """
    Include persistence features, as well as logging of task invocation.
    """
    abstract = True


@task(base=_BaseTask)
def change_bulk_mailing_handler(**kwargs):
    course_key = kwargs.pop('course_key')
    from lms.djangoapps.instructor_task.api import change_bulk_mailing
    change_bulk_mailing(course_key)
