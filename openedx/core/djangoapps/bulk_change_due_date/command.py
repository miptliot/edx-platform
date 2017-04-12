# -*- coding: utf-8 -*-
import logging
from django.core.management.base import BaseCommand, CommandError
from xmodule.modulestore.django import modulestore
from .utils import choose_date_changer


class Command(BaseCommand):
    """
    Examples:
    python manage.py lms cohort_change_due --course_key=course-v1:test_o+test_n+test_r --add_days=30 --cohort=my_cohort
    python manage.py lms cohort_change_due --course_key=course-v1:test_o+test_n+test_r --set_date=2016/12/12 --cohort=my_cohort
    python manage.py lms cohort_change_due
        --block_key=block-v1:test_o+test_n+test_r+type@problem+block@b725c8e540884a7890e0711b3f59a0aa
        --set_date="2016/12/10"
        --user=test1@test1.com

    """
    help = u"""
    Changes due date for given problem for given cohort or user
    """ + u"""
    Команде нужно указать 3 параметра: для кого менять, где менять и на когда менять
    Кто:
        --user={username / email},
        --cohort={name/id[ не тестировал]}
    Где:
        --block_key={Location проблемы из STAFF DEBUG INFO в LMS}
        --course_key={id курса, например 'course-v1:test_o+test_n+test_r'}
    Когда:
        --set_date={дата формата 2017/01/31}
        --add_days={int добавить дней. Команда с этой опцией не кумулятивна.}
    """

    def add_arguments(self, parser):
        parser.add_argument('--block_key', dest='block_key')
        parser.add_argument('--course_key', dest='course_key')

        parser.add_argument('--add_days', dest='add_days')
        parser.add_argument('--set_date', dest='set_date')

        parser.add_argument('--cohort', dest='cohort')
        parser.add_argument('--user', dest='user')

    def handle(self, **options):
        store = modulestore()

        who_keys = ('cohort', 'user')
        where_keys = ('block_key', 'course_key')
        when_keys = ('add_days', 'set_date')

        who_key, who_val = self._exist_n_unique(options, who_keys)
        where_key, where_val = self._exist_n_unique(options, where_keys)
        when_key, when_val = self._exist_n_unique(options, when_keys)

        choose_keys = [who_key, where_key, when_key]
        changer_wrap = choose_date_changer(choose_keys)
        try:
            changer = changer_wrap(who_val, where_val, when_val, store, stdout=self.stdout)
            changer.change_due()
            changer.logging()
        except ValueError as e:
            logging.error(e.message)
            raise CommandError("Command failed. Message:{}".format(e.message))
        self.stdout.write("Successfully changed date.")
        self.stdout.write(changer.logging_message)
        self.stdout.write(str(type(changer)))

    @staticmethod
    def _exist_n_unique(container, keys):
        """
        Проверяет что в контейнере для одного и только одного ключа из данных
        есть not-None значение
        :return: key
        """
        exist_pairs = [(k, container[k]) for k in keys if container[k]]
        if len(exist_pairs) != 1:
            raise CommandError("""
                Non unique value for keys = {keys}. Ambiguous command.
                {dict}
            """.format(keys=keys, dict=exist_pairs))
        single_key = exist_pairs[0][0]
        return single_key, container[single_key]
