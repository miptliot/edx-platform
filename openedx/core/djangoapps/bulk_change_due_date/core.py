# -*- coding: utf-8 -*-
import dateutil
from datetime import timedelta
import logging

from django.utils.timezone import utc
from opaque_keys.edx.keys import CourseKey, UsageKey

from lms.djangoapps.instructor.views.tools import require_student_from_identifier, set_due_date_extension
from openedx.core.djangoapps.course_groups.cohorts import get_cohort_by_id, get_cohort_by_name
from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore


class DateChanger(object):
    """
    Выполняет сдвиг дат для пользователя(-ей), блока(-ов) и нового срока(-ов). Не должен использоваться без
    трех примесей, каждая из которых реализует соответственно группу юзеров, группу блоков и группу сроков.
    Может использоваться в web view либо в команде
    """
    def __init__(self, who, where, when, store=None, stdout=None):
        self.who = who  # user or cohort identifier
        self.when = when  # date to set or days to add
        self.where = where  # xblock or course location
        self.stdout = stdout
        self.store = store or modulestore()

    def set_stdout(self, stdout):
        self.stdout = stdout

    @staticmethod
    def _get_xblock_course(xblock, store=None):
        """
        Находит для данного xblock корень-course
        :param xblock:
        :return: course
        """
        item = xblock
        if store:
            course_key = xblock.location.course_key
            try:
                course = store.get_course(course_key)
                return course
            except ValueError:
                raise RuntimeError("No course for course_key '{}'".format(str(course_key)))

        #Пытаемсся найти итерациями по get_parent
        arbitrary_iter_number = 10
        for _ in range(arbitrary_iter_number):
            if item.category == "course":
                return item
            item = item.get_parent()
        raise RuntimeError("Did not find course root for xblock")

    @staticmethod
    def _parse_date(date_str):
        """
        Парсит строку-дату в объект
        :param date_str:
        :return:
        """
        try:
            date = dateutil.parser.parse(date_str, dayfirst=True).replace(tzinfo=utc)
        except ValueError:
            raise RuntimeError(
                "Date {} not recognized".format(date_str)
            )
        return date

    @classmethod
    def wrap(cls):
        def inner_wrap(*args, **kwargs):
            return cls(*args, **kwargs)

        return inner_wrap

    @property
    def users_group(self):
        raise NotImplementedError

    @property
    def xblock_group(self):
        raise NotImplementedError

    @property
    def dates_group(self):
        raise NotImplementedError

    @property
    def course(self):
        raise NotImplementedError

    def change_due(self):
        for user in self.users_group:
            for num, xblock in enumerate(self.xblock_group):
                date = self.dates_group[num]
                is_enrolled = CourseEnrollment.is_enrolled(user, self.course.id)
                if not is_enrolled:
                    raise RuntimeError("User {} is not enrolled on course with key {}".format(
                        user.username,
                        self.course.id))

                set_due_date_extension(self.course, xblock, user, date)

    def logging(self):
        all_changes = []
        template = u"block '{block}'('{block_name}') for user '{user}': set due '{date}';"
        for user in self.users_group:
            for num, xblock in enumerate(self.xblock_group):
                date = self.dates_group[num]
                all_changes.append(template.format(
                    block=str(xblock.location),
                    block_name=unicode(xblock.display_name),
                    date=str(date),
                    user=user.username
                ))
        self.logging_message = "\n".join(x for x in all_changes)
        logging.info(self.logging_message)


class BlockMixin(object):
    @property
    def xblock_group(self):
        try:
            return self._xblock_group
        except AttributeError:
            pass
        usage_key = UsageKey.from_string(self.where)
        xblock = self.store.get_item(usage_key)
        if not getattr(self, "_course", False):
            self._course = self._get_xblock_course(xblock)
        self._xblock_group = self._breadth_search(xblock)
        return self._xblock_group

    def _breadth_search(self, block):
        num_item = 0
        items = [block]
        while num_item<len(items):
            current = items[num_item]
            items.extend(current.get_children())
            num_item += 1
        return items

    @property
    def course(self):
        try:
            return self._course
        except AttributeError:
            xblock = self.xblock_group[0]
            self._course = self._get_xblock_course(xblock)
            return self._course


class CourseMixin(object):
    """
    IMPORTANT
    При выборе блоков, для которых меняются даты, делается проверка на наличие поля due.
    У problems такого поля нет, поэтому в список итемов попадают уже Subsection, а не отдельные
    problem.
    """
    @property
    def xblock_group(self):
        try:
            return self._xblock_group
        except AttributeError:
            pass

        course_key = CourseKey.from_string(self.where)
        course = self.store.get_course(course_key)
        if not getattr(self, "_course", False):
            self._course = course

        items = self.store.get_items(course_key)
        items = [x for x in items if (getattr(x, "due", False) and x.format)]
        children = []
        for x in items:
            if x.category == "vertical":
                children.extend(x.get_children())
        items.extend(children)

        if self.stdout:
            self.stdout.write(";; ".join(str(x.display_name) for x in items))
        self._xblock_group = items
        return self._xblock_group

    @property
    def course(self):
        try:
            return self._course
        except AttributeError:
            pass
        course_key = CourseKey.from_string(self.where)
        self._course = self.store.get_course(course_key)
        return self._course


class UserMixin(object):
    @property
    def users_group(self):
        try:
            return self._users_group
        except AttributeError:
            pass
        self._users_group = [require_student_from_identifier(self.who)]
        return self._users_group


class CohortMixin(object):
    def _get_cohort(self, cohort_id_or_name):
        course_key = self.course.id
        try:
            cohort = get_cohort_by_name(course_key,cohort_id_or_name)
            return cohort
        except Exception as e:
            pass
        try:
            cohort = get_cohort_by_id(course_key, cohort_id_or_name)
            return cohort
        except Exception as e:
            raise RuntimeError("Didn't find cohort")

    @property
    def users_group(self):
        try:
            return self._users_group
        except AttributeError:
            pass
        cohort = self._get_cohort(self.who)
        self._users_group = list(cohort.users.all())
        return self._users_group


class SetDateMixin(object):
    @property
    def dates_group(self):
        try:
            return self._dates_group
        except AttributeError:
            pass
        self._dates_group = [self._parse_date(self.when)]*len(self.xblock_group)
        return self._dates_group


class AddDaysMixin(object):
    """
    IMPORTANT
    При текущей реализации прибавление дней не кумулятивно -
    в качестве базы берется значение due самого xblock, а не
    StudentFieldOverride, поэтому, если выполнить команду дважды,
    результат не изменится.
    """

    @property
    def dates_group(self):
        try:
            return self._dates_group
        except AttributeError:
            pass
        xblocks = self.xblock_group
        dates = [x.due for x in xblocks]
        dates = [d + timedelta(days=int(self.when)) for d in dates]
        self._dates_group = dates
        return self._dates_group


class UserProblemSetDate(UserMixin, BlockMixin, SetDateMixin, DateChanger):
    pass


class UserProblemAddDays(UserMixin, BlockMixin, AddDaysMixin, DateChanger):
    pass


class UserCourseSetDate(UserMixin, CourseMixin, SetDateMixin, DateChanger):
    pass


class UserCourseAddDays(UserMixin, CourseMixin, AddDaysMixin, DateChanger):
    pass


class CohortProblemSetDate(CohortMixin, BlockMixin, SetDateMixin, DateChanger):
    pass


class CohortProblemAddDays(CohortMixin, BlockMixin, AddDaysMixin, DateChanger):
    pass


class CohortCourseSetDate(CohortMixin, CourseMixin, SetDateMixin, DateChanger):
    pass


class CohortCourseAddDays(CohortMixin, CourseMixin, AddDaysMixin, DateChanger):
    pass

