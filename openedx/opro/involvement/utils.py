from base64 import b64encode
import json
import requests

from django.conf import settings
from django.contrib.auth.models import User

from openedx.opro.involvement.models import UserCourseInvolvement, InvolvementLink, UserVisitInvolvementLink

platform_name = getattr(settings, 'EXAMUS_PLATFORM_NAME')
platform_password = getattr(settings, 'EXAMUS_PLATFORM_PASSWORD')
examus_base_url = getattr(settings, 'EXAMUS_BASE_URL')


def check_involvement(course_id, location, username):
    if not platform_name or not platform_password or not examus_base_url:
        return
    user = User.objects.get(username=username)
    uci = UserCourseInvolvement.objects.filter(user=user, is_active=True)
    if uci:
        user_and_pass = b64encode(b"{}:{}".format(platform_name, platform_password)).decode("ascii")
        headers = {'Authorization': 'Basic %s' % user_and_pass}
        link = InvolvementLink.objects.filter(course_key=course_id, usage_key=location).first()
        if not link:
            r = requests.get('{}/link/'.format(examus_base_url), headers=headers)
            link_id = json.loads(r.text)['id']
            link = InvolvementLink.objects.create(link_id=link_id, course_key=course_id, usage_key=location)
        link_id = link.link_id
        visit = UserVisitInvolvementLink.objects.create(link=link, user=user)
        json_parameters = {"link_id": link_id, "visit_id": str(visit.id)}
        s = requests.post('{}/link/auth/'.format(examus_base_url), headers=headers, json=json_parameters)
        token = json.loads(s.text)['token']
        return token
