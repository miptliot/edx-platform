import base64
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _


User = get_user_model()


def openedu_email(html_msg, plaintext_msg, email, course_email, course_title, course_url):
    to_course_html_msg = _('''<br/><p>You received this email because you are enrolled in the course "{course_title}"
    on the platform "Openedu". If you want to continue learning
    follow <a href="{course_url}courseware">this link.</a></p>''').format(
        course_title=course_title,
        course_url=course_url,
    )
    to_course_plaintext_msg = _('''You received this email because you are enrolled in the course "{course_title}"
    on the platform "Openedu". If you want to continue learning
    follow this link {course_url}courseware.''').format(
        course_title=course_title,
        course_url=course_url,
    )
    html_msg = _('{html_msg} {to_course_html_msg}').format(html_msg=html_msg, to_course_html_msg=to_course_html_msg)
    plaintext_msg = _('{plaintext_msg} {to_course_plaintext_msg}').format(plaintext_msg=plaintext_msg, to_course_plaintext_msg=to_course_plaintext_msg)
    unsubscribe_headers = dict()
    username = User.objects.filter(email=email)[0].username
    unsubscribe_hash = base64.b64encode("{username}+{course_id}".format(
        username=username, course_id=course_email.course_id.html_id())
    )
    unsubscribe_url = '%s%s' % ("{}/unsubscribe/".format(settings.PLP_URL), unsubscribe_hash)
    unsubscribe_headers['List-Unsubscribe'] = '<{}>'.format(unsubscribe_url)

    html_msg = _('''{html_msg} For unsubscribe follow
    <a href="{unsubscribe_url}">this link.</a>''').format(
        html_msg=html_msg,
        unsubscribe_url=unsubscribe_url
    )
    plaintext_msg = _('''{plaintext_msg} For unsubscribe follow
    this link {unsubscribe_url}.''').format(
        plaintext_msg=plaintext_msg,
        unsubscribe_url=unsubscribe_url
    )

    return html_msg, plaintext_msg, unsubscribe_headers


def openedu_format_address(course_title_no_quotes):
    from_addr = _('"Course {course_title}" <{from_email}>').format(
            course_title=course_title_no_quotes,
            from_email=settings.BULK_EMAIL_DEFAULT_FROM_EMAIL
    )
    return from_addr
