import json
import pytz
import requests
from datetime import datetime

from logging import getLogger

from django.core.cache import cache
from django.dispatch import receiver

from student.models import UserProfile, ENROLL_STATUS_CHANGE, EnrollStatusChange
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import CourseLocator
from xmodule.modulestore.django import modulestore

log = getLogger(__name__)


def stsos_data(kwargs):
    cache_key = 'User_ESIA_ID_{}'.format(kwargs['user_id'])
    esia_id = cache.get(cache_key)
    if not esia_id:
        up = UserProfile.objects.filter(user__id=kwargs['user_id']).first()
        if up:
            try:
                esia_id = json.loads(up.goals).get('sud')
            except:
                esia_id = 'null'
            if not esia_id:
                esia_id = 'null'
        else:
            esia_id = 'null'
        cache.set(cache_key, esia_id, 1800)
    if esia_id == 'null':
        return
    stsos_cache_key = "Stsos_Course_Ids_Json"
    stsos_ids = cache.get(stsos_cache_key)
    if not stsos_ids:
        stsos_ids = requests.get('https://openedu.ru/api/courses/stsos_ids/?format=json').json()
        cache.set(stsos_cache_key, stsos_ids, 7200)
    prefix, plp_course_id, course_run = kwargs['course_id'].split('+')
    if not plp_course_id in stsos_ids:
        return
    stsos_id = stsos_ids[plp_course_id]
    stsos = dict()
    stsos['courseId'] = stsos_id
    stsos['sessionId'] = kwargs['course_id']
    stsos['usiaId'] = esia_id
    stsos['date'] = kwargs['modified'].strftime('%Y-%m-%dT%H:%M:%S%z')
    stsos['rating'] = None
    if 'weighted_earned' in kwargs.keys() and 'weighted_possible' in kwargs.keys():
        try:
            weighted_earned = float(kwargs['weighted_earned'])
            weighted_possible = float(kwargs['weighted_possible'])
            stsos['rating'] = int(weighted_earned/weighted_possible*100)
        except:
            pass
    stsos['progress'] = None
    stsos['proctored'] = None
    course_key = CourseLocator.from_string(kwargs['course_id'])
    scored_block_usage_key = UsageKey.from_string(kwargs['usage_id']).replace(course_key=course_key)
    descriptor = None
    try:
        descriptor = modulestore().get_item(scored_block_usage_key)
        checkpoint_name = descriptor.display_name
    except:
        checkpoint_name = None
    if not descriptor:
        return
    if not descriptor.graded:
        return
    stsos['checkpointName'] = checkpoint_name
    stsos['checkpointId'] = kwargs['usage_id']
    stsos['type'] = 'problem_check'
    log.info(json.dumps(stsos))


def stsos_enroll_data(kwargs):
    event = kwargs['event']
    if not event == EnrollStatusChange.enroll:
        return
    # TODO: DRY!
    cache_key = 'User_ESIA_ID_{}'.format(kwargs['user'].id)
    esia_id = cache.get(cache_key)
    if not esia_id:
        up = UserProfile.objects.filter(user=kwargs['user']).first()
        if up:
            try:
                esia_id = json.loads(up.goals).get('sud')
            except:
                esia_id = 'null'
            if not esia_id:
                esia_id = 'null'
        else:
            esia_id = 'null'
        cache.set(cache_key, esia_id, 1800)
    if esia_id == 'null':
        return
    stsos_cache_key = "Stsos_Course_Ids_Json"
    stsos_ids = cache.get(stsos_cache_key)
    if not stsos_ids:
        stsos_ids = requests.get('https://openedu.ru/api/courses/stsos_ids/?format=json').json()
        cache.set(stsos_cache_key, stsos_ids, 7200)
    prefix, plp_course_id, course_run = str(kwargs['course_id']).split('+')
    if not plp_course_id in stsos_ids:
        return
    stsos_id = stsos_ids[plp_course_id]
    stsos = dict()
    stsos['courseId'] = stsos_id
    stsos['sessionId'] = str(kwargs['course_id'])
    stsos['usiaId'] = esia_id
    stsos['enrollDate'] = datetime.utcnow().replace(tzinfo=pytz.UTC).strftime('%Y-%m-%dT%H:%M:%S%z')
    stsos['type'] = 'enroll'
    log.info(json.dumps(stsos))


def stsos_progress_data(kwargs):
    progress = kwargs.get('progress',{}).get('percent')
    if not progress:
        return
    cache_key = 'User_ESIA_ID_{}'.format(kwargs['user'].id)
    esia_id = cache.get(cache_key)
    if not esia_id:
        up = UserProfile.objects.filter(user=kwargs['user']).first()
        if up:
            try:
                esia_id = json.loads(up.goals).get('sud')
            except:
                esia_id = 'null'
            if not esia_id:
                esia_id = 'null'
        else:
            esia_id = 'null'
        cache.set(cache_key, esia_id, 1800)
    if esia_id == 'null':
        return
    stsos_cache_key = "Stsos_Course_Ids_Json"
    stsos_ids = cache.get(stsos_cache_key)
    if not stsos_ids:
        stsos_ids = requests.get('https://openedu.ru/api/courses/stsos_ids/?format=json').json()
        cache.set(stsos_cache_key, stsos_ids, 7200)
    prefix, plp_course_id, course_run = str(kwargs['course_id']).split('+')
    if not plp_course_id in stsos_ids:
        return
    stsos_id = stsos_ids[plp_course_id]
    stsos = dict()
    stsos['courseId'] = stsos_id
    stsos['sessionId'] = str(kwargs['course_id'])
    stsos['usiaId'] = esia_id
    stsos['progress'] = int(float(progress)*100)
    stsos['type'] = 'progress'
    log.info(json.dumps(stsos))
