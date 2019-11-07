"""Certificates API

This is a Python API for generating certificates asynchronously.
Other Django apps should use the API functions defined in this module
rather than importing Django models directly.
"""
import logging
import pytz
from datetime import datetime
from uuid import uuid4
import urllib
import binascii
import os
import tempfile
import subprocess

from django.conf import settings
from django.urls import reverse
from django.db.models import Q
from opaque_keys.edx.django.models import CourseKeyField
from opaque_keys.edx.keys import CourseKey

from branding import api as branding_api
from lms.djangoapps.certificates.models import (
    CertificateGenerationConfiguration,
    CertificateGenerationCourseSetting,
    CertificateInvalidation,
    CertificateStatuses,
    CertificateTemplate,
    CertificateTemplateAsset,
    ExampleCertificateSet,
    GeneratedCertificate,
    certificate_status_for_student,
    get_certificate,
    CertificateHtmlViewConfiguration,
    CertificateSocialNetworks
)
from lms.djangoapps.certificates.queue import XQueueCertInterface
from eventtracking import tracker
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from util.organizations_helpers import get_course_organization_id
from xmodule.modulestore.django import modulestore
from django.utils import translation
from django.http import HttpResponse, Http404
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from django.contrib.auth.models import User
from opaque_keys import InvalidKeyError
from edxmako.shortcuts import render_to_response
from courseware.courses import get_course_by_id
from courseware.access import has_access
from openedx.core.djangoapps.certificates.api import display_date_for_certificate, certificates_viewable_for_course
from openedx.core.djangoapps.catalog.utils import get_course_run_details
from openedx.core.djangoapps.lang_pref.api import get_closest_released_language
from openedx.core.lib.courses import course_image_url
from util import organizations_helpers as organization_api
from util.date_utils import strftime_localized
from django.utils.encoding import smart_str
from student.models import LinkedInAddToProfileConfiguration
from badges.events.course_complete import get_completion_badge
from badges.utils import badges_enabled
from edxmako.template import Template
from django.template import RequestContext
from openedx.core.storage import get_storage


log = logging.getLogger("edx.certificate")
MODES = GeneratedCertificate.MODES
INVALID_CERTIFICATE_TEMPLATE_PATH = 'certificates/invalid.html'
_ = translation.ugettext


class FakeRequest(object):
    user = None
    site = None
    META = {}
    GET = {}
    POST = {}

    def __init__(self, user, site=None):
        self.user = user
        self.site = site

    def is_secure(self):
        return True

    def build_absolute_uri(self, location=None):
        return ''


def is_passing_status(cert_status):
    """
    Given the status of a certificate, return a boolean indicating whether
    the student passed the course.  This just proxies to the classmethod
    defined in models.py
    """
    return CertificateStatuses.is_passing_status(cert_status)


def format_certificate_for_user(username, cert):
    """
    Helper function to serialize an user certificate.

    Arguments:
        username (unicode): The identifier of the user.
        cert (GeneratedCertificate): a user certificate

    Returns: dict
    """
    return {
        "username": username,
        "course_key": cert.course_id,
        "type": cert.mode,
        "status": cert.status,
        "grade": cert.grade,
        "created": cert.created_date,
        "modified": cert.modified_date,
        "is_passing": is_passing_status(cert.status),

        # NOTE: the download URL is not currently being set for webview certificates.
        # In the future, we can update this to construct a URL to the webview certificate
        # for courses that have this feature enabled.
        "download_url": (
            cert.download_url or get_certificate_url(cert.user.id, cert.course_id)
            if cert.status == CertificateStatuses.downloadable
            else None
        ),
    }


def get_certificates_for_user(username):
    """
    Retrieve certificate information for a particular user.

    Arguments:
        username (unicode): The identifier of the user.

    Returns: list

    Example Usage:
    >>> get_certificates_for_user("bob")
    [
        {
            "username": "bob",
            "course_key": CourseLocator('edX', 'DemoX', 'Demo_Course', None, None),
            "type": "verified",
            "status": "downloadable",
            "download_url": "http://www.example.com/cert.pdf",
            "grade": "0.98",
            "created": 2015-07-31T00:00:00Z,
            "modified": 2015-07-31T00:00:00Z
        }
    ]

    """
    return [
        format_certificate_for_user(username, cert)
        for cert in GeneratedCertificate.eligible_certificates.filter(user__username=username).order_by("course_id")
    ]


def get_certificate_for_user(username, course_key):
    """
    Retrieve certificate information for a particular user for a specific course.

    Arguments:
        username (unicode): The identifier of the user.
        course_key (CourseKey): A Course Key.
    Returns: dict
    """
    try:
        cert = GeneratedCertificate.eligible_certificates.get(
            user__username=username,
            course_id=course_key
        )
    except GeneratedCertificate.DoesNotExist:
        return None
    return format_certificate_for_user(username, cert)


def generate_user_certificates(student, course_key, course=None, insecure=False, generation_mode='batch',
                               forced_grade=None):
    """
    It will add the add-cert request into the xqueue.

    A new record will be created to track the certificate
    generation task.  If an error occurs while adding the certificate
    to the queue, the task will have status 'error'. It also emits
    `edx.certificate.created` event for analytics.

    Args:
        student (User)
        course_key (CourseKey)

    Keyword Arguments:
        course (Course): Optionally provide the course object; if not provided
            it will be loaded.
        insecure - (Boolean)
        generation_mode - who has requested certificate generation. Its value should `batch`
        in case of django command and `self` if student initiated the request.
        forced_grade - a string indicating to replace grade parameter. if present grading
                       will be skipped.
    """
    xqueue = XQueueCertInterface()
    if insecure:
        xqueue.use_https = False

    if not course:
        course = modulestore().get_course(course_key, depth=0)

    generate_pdf = not has_any_active_web_certificate(course)

    cert = xqueue.add_cert(
        student,
        course_key,
        course=course,
        generate_pdf=generate_pdf,
        forced_grade=forced_grade
    )
    # If cert_status is not present in certificate valid_statuses (for example unverified) then
    # add_cert returns None and raises AttributeError while accesing cert attributes.
    if cert is None:
        return

    if CertificateStatuses.is_passing_status(cert.status):
        create_pdf_for_certificate(cert)
        emit_certificate_event('created', student, course_key, course, {
            'user_id': student.id,
            'course_id': unicode(course_key),
            'certificate_id': cert.verify_uuid,
            'enrollment_mode': cert.mode,
            'generation_mode': generation_mode
        })
    return cert.status


def regenerate_user_certificates(student, course_key, course=None,
                                 forced_grade=None, template_file=None, insecure=False):
    """
    It will add the regen-cert request into the xqueue.

    A new record will be created to track the certificate
    generation task.  If an error occurs while adding the certificate
    to the queue, the task will have status 'error'.

    Args:
        student (User)
        course_key (CourseKey)

    Keyword Arguments:
        course (Course): Optionally provide the course object; if not provided
            it will be loaded.
        grade_value - The grade string, such as "Distinction"
        template_file - The template file used to render this certificate
        insecure - (Boolean)
    """
    xqueue = XQueueCertInterface()
    if insecure:
        xqueue.use_https = False

    if not course:
        course = modulestore().get_course(course_key, depth=0)

    generate_pdf = not has_any_active_web_certificate(course)
    log.info(
        "Started regenerating certificates for user %s in course %s with generate_pdf status: %s",
        student.username, unicode(course_key), generate_pdf
    )

    cert = xqueue.regen_cert(
        student,
        course_key,
        course=course,
        forced_grade=forced_grade,
        template_file=template_file,
        generate_pdf=generate_pdf
    )
    create_pdf_for_certificate(cert)
    return cert


def certificate_downloadable_status(student, course_key):
    """
    Check the student existing certificates against a given course.
    if status is not generating and not downloadable or error then user can view the generate button.

    Args:
        student (user object): logged-in user
        course_key (CourseKey): ID associated with the course

    Returns:
        Dict containing student passed status also download url, uuid for cert if available
    """
    current_status = certificate_status_for_student(student, course_key)

    # If the certificate status is an error user should view that status is "generating".
    # On the back-end, need to monitor those errors and re-submit the task.

    generated_certificate = get_certificate(student, course_key)

    response_data = {
        'is_downloadable': False,
        'is_generating': True if current_status['status'] in [CertificateStatuses.generating,
                                                              CertificateStatuses.error] else False,
        'is_unverified': True if current_status['status'] == CertificateStatuses.unverified else False,
        'download_url': None,
        'uuid': None,
        'grade': generated_certificate.grade if generated_certificate else None
    }
    may_view_certificate = CourseOverview.get_from_id(course_key).may_certify()

    if current_status['status'] == CertificateStatuses.downloadable and may_view_certificate:
        response_data['is_downloadable'] = True
        response_data['download_url'] = current_status['download_url'] or get_certificate_url(student.id, course_key)
        response_data['uuid'] = current_status['uuid']

    return response_data


def set_cert_generation_enabled(course_key, is_enabled):
    """Enable or disable self-generated certificates for a course.

    There are two "switches" that control whether self-generated certificates
    are enabled for a course:

    1) Whether the self-generated certificates feature is enabled.
    2) Whether self-generated certificates have been enabled for this particular course.

    The second flag should be enabled *only* when someone has successfully
    generated example certificates for the course.  This helps avoid
    configuration errors (for example, not having a template configured
    for the course installed on the workers).  The UI for the instructor
    dashboard enforces this constraint.

    Arguments:
        course_key (CourseKey): The course identifier.

    Keyword Arguments:
        is_enabled (boolean): If provided, enable/disable self-generated
            certificates for this course.

    """
    CertificateGenerationCourseSetting.set_self_generatation_enabled_for_course(course_key, is_enabled)
    cert_event_type = 'enabled' if is_enabled else 'disabled'
    event_name = '.'.join(['edx', 'certificate', 'generation', cert_event_type])
    tracker.emit(event_name, {
        'course_id': unicode(course_key),
    })
    if is_enabled:
        log.info(u"Enabled self-generated certificates for course '%s'.", unicode(course_key))
    else:
        log.info(u"Disabled self-generated certificates for course '%s'.", unicode(course_key))


def is_certificate_invalid(student, course_key):
    """Check that whether the student in the course has been invalidated
    for receiving certificates.

    Arguments:
        student (user object): logged-in user
        course_key (CourseKey): The course identifier.

    Returns:
        Boolean denoting whether the student in the course is invalidated
        to receive certificates
    """
    is_invalid = False
    certificate = GeneratedCertificate.certificate_for_student(student, course_key)
    if certificate is not None:
        is_invalid = CertificateInvalidation.has_certificate_invalidation(student, course_key)

    return is_invalid


def cert_generation_enabled(course_key):
    """Check whether certificate generation is enabled for a course.

    There are two "switches" that control whether self-generated certificates
    are enabled for a course:

    1) Whether the self-generated certificates feature is enabled.
    2) Whether self-generated certificates have been enabled for this particular course.

    Certificates are enabled for a course only when both switches
    are set to True.

    Arguments:
        course_key (CourseKey): The course identifier.

    Returns:
        boolean: Whether self-generated certificates are enabled
            for the course.

    """
    return (
        CertificateGenerationConfiguration.current().enabled and
        CertificateGenerationCourseSetting.is_self_generation_enabled_for_course(course_key)
    )


def generate_example_certificates(course_key):
    """Generate example certificates for a course.

    Example certificates are used to validate that certificates
    are configured correctly for the course.  Staff members can
    view the example certificates before enabling
    the self-generated certificates button for students.

    Several example certificates may be generated for a course.
    For example, if a course offers both verified and honor certificates,
    examples of both types of certificate will be generated.

    If an error occurs while starting the certificate generation
    job, the errors will be recorded in the database and
    can be retrieved using `example_certificate_status()`.

    Arguments:
        course_key (CourseKey): The course identifier.

    Returns:
        None

    """
    xqueue = XQueueCertInterface()
    for cert in ExampleCertificateSet.create_example_set(course_key):
        xqueue.add_example_cert(cert)


def example_certificates_status(course_key):
    """Check the status of example certificates for a course.

    This will check the *latest* example certificate task.
    This is generally what we care about in terms of enabling/disabling
    self-generated certificates for a course.

    Arguments:
        course_key (CourseKey): The course identifier.

    Returns:
        list

    Example Usage:

        >>> from lms.djangoapps.certificates import api as certs_api
        >>> certs_api.example_certificate_status(course_key)
        [
            {
                'description': 'honor',
                'status': 'success',
                'download_url': 'http://www.example.com/abcd/honor_cert.pdf'
            },
            {
                'description': 'verified',
                'status': 'error',
                'error_reason': 'No template found!'
            }
        ]

    """
    return ExampleCertificateSet.latest_status(course_key)


def _safe_course_key(course_key):
    if not isinstance(course_key, CourseKey):
        return CourseKey.from_string(course_key)
    return course_key


def _course_from_key(course_key):
    return CourseOverview.get_from_id(_safe_course_key(course_key))


def _certificate_html_url(user_id, course_id, uuid):
    if uuid:
        return reverse('certificates:render_cert_by_uuid', kwargs={'certificate_uuid': uuid})
    elif user_id and course_id:
        kwargs = {"user_id": str(user_id), "course_id": unicode(course_id)}
        return reverse('certificates:html_view', kwargs=kwargs)
    return ''


def _certificate_download_url(user_id, course_id):
    try:
        user_certificate = GeneratedCertificate.eligible_certificates.get(
            user=user_id,
            course_id=_safe_course_key(course_id)
        )
        return user_certificate.download_url
    except GeneratedCertificate.DoesNotExist:
        log.critical(
            'Unable to lookup certificate\n'
            'user id: %d\n'
            'course: %s', user_id, unicode(course_id)
        )
    return ''


def has_html_certificates_enabled(course):
    if not settings.FEATURES.get('CERTIFICATES_HTML_VIEW', False):
        return False
    return course.cert_html_view_enabled


def get_certificate_url(user_id=None, course_id=None, uuid=None):
    url = ''

    course = _course_from_key(course_id)
    if not course:
        return url

    if has_html_certificates_enabled(course) and has_any_active_web_certificate(course):
        url = _certificate_html_url(user_id, course_id, uuid)
    else:
        url = _certificate_download_url(user_id, course_id)
    return url


def has_any_active_web_certificate(course):
    if hasattr(course, 'has_any_active_web_certificate'):
        return course.has_any_active_web_certificate

    return get_active_web_certificate(course)


def get_active_web_certificate(course, is_preview_mode=None):
    """
    Retrieves the active web certificate configuration for the specified course
    """
    certificates = getattr(course, 'certificates', {})
    configurations = certificates.get('certificates', [])
    for config in configurations:
        if config.get('is_active') or is_preview_mode:
            return config
    return None


def get_certificate_template(course_key, mode, language):
    """
    Retrieves the custom certificate template based on course_key, mode, and language.
    """
    template = None
    # fetch organization of the course
    org_id = get_course_organization_id(course_key)

    # only consider active templates
    active_templates = CertificateTemplate.objects.filter(is_active=True)

    if org_id and mode:  # get template by org, mode, and key
        org_mode_and_key_templates = active_templates.filter(
            organization_id=org_id,
            mode=mode,
            course_key=course_key
        )
        template = get_language_specific_template_or_default(language, org_mode_and_key_templates)

    # since no template matched that course_key, only consider templates with empty course_key
    empty_course_key_templates = active_templates.filter(course_key=CourseKeyField.Empty)
    if not template and org_id and mode:  # get template by org and mode
        org_and_mode_templates = empty_course_key_templates.filter(
            organization_id=org_id,
            mode=mode
        )
        template = get_language_specific_template_or_default(language, org_and_mode_templates)
    if not template and org_id:  # get template by only org
        org_templates = empty_course_key_templates.filter(
            organization_id=org_id,
            mode=None
        )
        template = get_language_specific_template_or_default(language, org_templates)
    if not template and mode:  # get template by only mode
        mode_templates = empty_course_key_templates.filter(
            organization_id=None,
            mode=mode
        )
        template = get_language_specific_template_or_default(language, mode_templates)
    return template if template else None


def get_language_specific_template_or_default(language, templates):
    """
    Returns templates that match passed in language.
    Returns default templates If no language matches, or language passed is None
    """
    two_letter_language = _get_two_letter_language_code(language)
    language_or_default_templates = list(templates.filter(Q(language=two_letter_language) | Q(language=None) | Q(language='')))
    language_specific_template = get_language_specific_template(two_letter_language, language_or_default_templates)
    if language_specific_template:
        return language_specific_template
    else:
        return get_all_languages_or_default_template(language_or_default_templates)


def get_language_specific_template(language, templates):
    for template in templates:
        if template.language == language:
            return template
    return None


def get_all_languages_or_default_template(templates):
    for template in templates:
        if template.language == '':
            return template

    return templates[0] if templates else None


def _get_two_letter_language_code(language_code):
    """
    Shortens language to only first two characters (e.g. es-419 becomes es)
    This is needed because Catalog returns locale language which is not always a 2 letter code.
    """
    if language_code is None:
        return None
    elif language_code == '':
        return ''
    else:
        return language_code[:2]


def emit_certificate_event(event_name, user, course_id, course=None, event_data=None):
    """
    Emits certificate event.
    """
    event_name = '.'.join(['edx', 'certificate', event_name])
    if course is None:
        course = modulestore().get_course(course_id, depth=0)
    context = {
        'org_id': course.org,
        'course_id': unicode(course_id)
    }
    data = {
        'user_id': user.id,
        'course_id': unicode(course_id),
        'certificate_url': get_certificate_url(user.id, course_id)
    }
    event_data = event_data or {}
    event_data.update(data)

    with tracker.get_tracker().context(event_name, context):
        tracker.emit(event_name, event_data)


def get_asset_url_by_slug(asset_slug):
    """
    Returns certificate template asset url for given asset_slug.
    """
    asset_url = ''
    try:
        template_asset = CertificateTemplateAsset.objects.get(asset_slug=asset_slug)
        asset_url = template_asset.asset.url
    except CertificateTemplateAsset.DoesNotExist:
        pass
    return asset_url


def get_certificate_header_context(is_secure=True):
    """
    Return data to be used in Certificate Header,
    data returned should be customized according to the site configuration.
    """
    data = dict(
        logo_src=branding_api.get_logo_url(is_secure),
        logo_url=branding_api.get_base_url(is_secure),
    )

    return data


def get_certificate_footer_context():
    """
    Return data to be used in Certificate Footer,
    data returned should be customized according to the site configuration.
    """
    data = dict()

    # get Terms of Service and Honor Code page url
    terms_of_service_and_honor_code = branding_api.get_tos_and_honor_code_url()
    if terms_of_service_and_honor_code != branding_api.EMPTY_URL:
        data.update({'company_tos_url': terms_of_service_and_honor_code})

    # get Privacy Policy page url
    privacy_policy = branding_api.get_privacy_url()
    if privacy_policy != branding_api.EMPTY_URL:
        data.update({'company_privacy_url': privacy_policy})

    # get About page url
    about = branding_api.get_about_url()
    if about != branding_api.EMPTY_URL:
        data.update({'company_about_url': about})

    return data


def _update_context_with_basic_info(context, course_id, platform_name, configuration):
    """
    Updates context dictionary with basic info required before rendering simplest
    certificate templates.
    """
    context['platform_name'] = platform_name
    context['course_id'] = course_id

    # Update the view context with the default ConfigurationModel settings
    context.update(configuration.get('default', {}))

    # Translators:  'All rights reserved' is a legal term used in copyrighting to protect published content
    reserved = _("All rights reserved")
    context['copyright_text'] = u'&copy; {year} {platform_name}. {reserved}.'.format(
        year=datetime.now(pytz.timezone(settings.TIME_ZONE)).year,
        platform_name=platform_name,
        reserved=reserved
    )

    # Translators:  This text is bound to the HTML 'title' element of the page and appears
    # in the browser title bar when a requested certificate is not found or recognized
    context['document_title'] = _("Invalid Certificate")

    context['company_tos_urltext'] = _("Terms of Service & Honor Code")

    # Translators: A 'Privacy Policy' is a legal document/statement describing a website's use of personal information
    context['company_privacy_urltext'] = _("Privacy Policy")

    # Translators: This line appears as a byline to a header image and describes the purpose of the page
    context['logo_subtitle'] = _("Certificate Validation")

    # Translators: Accomplishments describe the awards/certifications obtained by students on this platform
    context['accomplishment_copy_about'] = _('About {platform_name} Accomplishments').format(
        platform_name=platform_name
    )

    # Translators:  This line appears on the page just before the generation date for the certificate
    context['certificate_date_issued_title'] = _("Issued On:")

    # Translators:  The Certificate ID Number is an alphanumeric value unique to each individual certificate
    context['certificate_id_number_title'] = _('Certificate ID Number')

    context['certificate_info_title'] = _('About {platform_name} Certificates').format(
        platform_name=platform_name
    )

    context['certificate_verify_title'] = _("How {platform_name} Validates Student Certificates").format(
        platform_name=platform_name
    )

    # Translators:  This text describes the validation mechanism for a certificate file (known as GPG security)
    context['certificate_verify_description'] = _('Certificates issued by {platform_name} are signed by a gpg key so '
                                                  'that they can be validated independently by anyone with the '
                                                  '{platform_name} public key. For independent verification, '
                                                  '{platform_name} uses what is called a '
                                                  '"detached signature"&quot;".').format(platform_name=platform_name)

    context['certificate_verify_urltext'] = _("Validate this certificate for yourself")

    # Translators:  This text describes (at a high level) the mission and charter the edX platform and organization
    context['company_about_description'] = _("{platform_name} offers interactive online classes and MOOCs.").format(
        platform_name=platform_name)

    context['company_about_title'] = _("About {platform_name}").format(platform_name=platform_name)

    context['company_about_urltext'] = _("Learn more about {platform_name}").format(platform_name=platform_name)

    context['company_courselist_urltext'] = _("Learn with {platform_name}").format(platform_name=platform_name)

    context['company_careers_urltext'] = _("Work at {platform_name}").format(platform_name=platform_name)

    context['company_contact_urltext'] = _("Contact {platform_name}").format(platform_name=platform_name)

    # Translators:  This text appears near the top of the certficate and describes the guarantee provided by edX
    context['document_banner'] = _("{platform_name} acknowledges the following student accomplishment").format(
        platform_name=platform_name
    )


def _render_invalid_certificate(course_id, platform_name, configuration):
    context = {}
    _update_context_with_basic_info(context, course_id, platform_name, configuration)
    return render_to_response(INVALID_CERTIFICATE_TEMPLATE_PATH, context)


def _get_user_certificate(request, user, course_key, course, preview_mode=None):
    """
    Retrieves user's certificate from db. Creates one in case of preview mode.
    Returns None if there is no certificate generated for given user
    otherwise returns `GeneratedCertificate` instance.
    """
    user_certificate = None
    if preview_mode:
        # certificate is being previewed from studio
        if has_access(request.user, 'instructor', course) or has_access(request.user, 'staff', course):
            if course.certificate_available_date and not course.self_paced:
                modified_date = course.certificate_available_date
            else:
                modified_date = datetime.now().date()
            user_certificate = GeneratedCertificate(
                mode=preview_mode,
                verify_uuid=unicode(uuid4().hex),
                modified_date=modified_date
            )
    elif certificates_viewable_for_course(course):
        # certificate is being viewed by learner or public
        try:
            user_certificate = GeneratedCertificate.eligible_certificates.get(
                user=user,
                course_id=course_key,
                status=CertificateStatuses.downloadable
            )
        except GeneratedCertificate.DoesNotExist:
            pass

    return user_certificate


def _get_catalog_data_for_course(course_key):
    """
    Retrieve data from the Discovery service necessary for rendering a certificate for a specific course.
    """
    course_certificate_settings = CertificateGenerationCourseSetting.get(course_key)
    if not course_certificate_settings:
        return {}

    catalog_data = {}
    course_run_fields = []
    if course_certificate_settings.language_specific_templates_enabled:
        course_run_fields.append('content_language')
    if course_certificate_settings.include_hours_of_effort:
        course_run_fields.extend(['weeks_to_complete', 'max_effort'])

    if course_run_fields:
        course_run_data = get_course_run_details(course_key, course_run_fields)
        if course_run_data.get('weeks_to_complete') and course_run_data.get('max_effort'):
            try:
                weeks_to_complete = int(course_run_data['weeks_to_complete'])
                max_effort = int(course_run_data['max_effort'])
                catalog_data['hours_of_effort'] = weeks_to_complete * max_effort
            except ValueError:
                log.exception('Error occurred while parsing course run details')
        catalog_data['content_language'] = course_run_data.get('content_language')

    return catalog_data


def _get_custom_template_and_language(course_id, course_mode, course_language):
    """
    Return the custom certificate template, if any, that should be rendered for the provided course/mode/language
    combination, along with the language that should be used to render that template.
    """
    closest_released_language = get_closest_released_language(course_language) if course_language else None
    template = get_certificate_template(course_id, course_mode, closest_released_language)

    if template and template.language:
        return (template, closest_released_language)
    elif template:
        return (template, settings.LANGUAGE_CODE)
    else:
        return (None, None)


def _update_organization_context(context, course):
    """
    Updates context with organization related info.
    """
    partner_long_name, organization_logo = None, None
    partner_short_name = course.display_organization if course.display_organization else course.org
    organizations = organization_api.get_course_organizations(course_id=course.id)
    if organizations:
        #TODO Need to add support for multiple organizations, Currently we are interested in the first one.
        organization = organizations[0]
        partner_long_name = organization.get('name', partner_long_name)
        partner_short_name = organization.get('short_name', partner_short_name)
        organization_logo = organization.get('logo', None)

    context['organization_long_name'] = partner_long_name
    context['organization_short_name'] = partner_short_name
    context['accomplishment_copy_course_org'] = partner_short_name
    context['organization_logo'] = organization_logo


def _update_course_context(request, context, course, course_key, platform_name):
    """
    Updates context dictionary with course info.
    """
    context['full_course_image_url'] = request.build_absolute_uri(course_image_url(course))
    course_title_from_cert = context['certificate_data'].get('course_title', '')
    accomplishment_copy_course_name = course_title_from_cert if course_title_from_cert else course.display_name
    context['accomplishment_copy_course_name'] = accomplishment_copy_course_name
    course_number = course.display_coursenumber if course.display_coursenumber else course.number
    context['course_number'] = course_number
    if context['organization_long_name']:
        # Translators:  This text represents the description of course
        context['accomplishment_copy_course_description'] = _('a course of study offered by {partner_short_name}, '
                                                              'an online learning initiative of '
                                                              '{partner_long_name}.').format(
            partner_short_name=context['organization_short_name'],
            partner_long_name=context['organization_long_name'],
            platform_name=platform_name)
    else:
        # Translators:  This text represents the description of course
        context['accomplishment_copy_course_description'] = _('a course of study offered by '
                                                              '{partner_short_name}.').format(
            partner_short_name=context['organization_short_name'],
            platform_name=platform_name)


def _update_context_with_user_info(context, user, user_certificate):
    """
    Updates context dictionary with user related info.
    """
    user_fullname = user.profile.name
    context['username'] = user.username
    context['course_mode'] = user_certificate.mode
    context['accomplishment_user_id'] = user.id
    context['accomplishment_copy_name'] = user_fullname
    context['accomplishment_copy_username'] = user.username

    context['accomplishment_more_title'] = _("More Information About {user_name}'s Certificate:").format(
        user_name=user_fullname
    )
    # Translators: This line is displayed to a user who has completed a course and achieved a certification
    context['accomplishment_banner_opening'] = _("{fullname}, you earned a certificate!").format(
        fullname=user_fullname
    )

    # Translators: This line congratulates the user and instructs them to share their accomplishment on social networks
    context['accomplishment_banner_congrats'] = _("Congratulations! This page summarizes what "
                                                  "you accomplished. Show it off to family, friends, and colleagues "
                                                  "in your social and professional networks.")

    # Translators: This line leads the reader to understand more about the certificate that a student has been awarded
    context['accomplishment_copy_more_about'] = _("More about {fullname}'s accomplishment").format(
        fullname=user_fullname
    )


def _update_social_context(request, context, course, user, user_certificate, platform_name):
    """
    Updates context dictionary with info required for social sharing.
    """
    share_settings = configuration_helpers.get_value("SOCIAL_SHARING_SETTINGS", settings.SOCIAL_SHARING_SETTINGS)
    context['facebook_share_enabled'] = share_settings.get('CERTIFICATE_FACEBOOK', False)
    context['facebook_app_id'] = configuration_helpers.get_value("FACEBOOK_APP_ID", settings.FACEBOOK_APP_ID)
    context['facebook_share_text'] = share_settings.get(
        'CERTIFICATE_FACEBOOK_TEXT',
        _("I completed the {course_title} course on {platform_name}.").format(
            course_title=context['accomplishment_copy_course_name'],
            platform_name=platform_name
        )
    )
    context['twitter_share_enabled'] = share_settings.get('CERTIFICATE_TWITTER', False)
    context['twitter_share_text'] = share_settings.get(
        'CERTIFICATE_TWITTER_TEXT',
        _("I completed a course at {platform_name}. Take a look at my certificate.").format(
            platform_name=platform_name
        )
    )

    share_url = request.build_absolute_uri(get_certificate_url(course_id=course.id, uuid=user_certificate.verify_uuid))
    context['share_url'] = share_url
    twitter_url = ''
    if context.get('twitter_share_enabled', False):
        twitter_url = 'https://twitter.com/intent/tweet?text={twitter_share_text}&url={share_url}'.format(
            twitter_share_text=smart_str(context['twitter_share_text']),
            share_url=urllib.quote_plus(smart_str(share_url))
        )
    context['twitter_url'] = twitter_url
    context['linked_in_url'] = None
    # If enabled, show the LinkedIn "add to profile" button
    # Clicking this button sends the user to LinkedIn where they
    # can add the certificate information to their profile.
    linkedin_config = LinkedInAddToProfileConfiguration.current()
    linkedin_share_enabled = share_settings.get('CERTIFICATE_LINKEDIN', linkedin_config.enabled)
    if linkedin_share_enabled:
        context['linked_in_url'] = linkedin_config.add_to_profile_url(
            course.id,
            course.display_name,
            user_certificate.mode,
            smart_str(share_url)
        )


def get_certificate_description(mode, certificate_type, platform_name):
    """
    :return certificate_type_description on the basis of current mode
    """
    certificate_type_description = None
    if mode == 'honor':
        # Translators:  This text describes the 'Honor' course certificate type.
        certificate_type_description = _("An {cert_type} certificate signifies that a "
                                         "learner has agreed to abide by the honor code established by {platform_name} "
                                         "and has completed all of the required tasks for this course under its "
                                         "guidelines.").format(cert_type=certificate_type,
                                                               platform_name=platform_name)
    elif mode == 'verified':
        # Translators:  This text describes the 'ID Verified' course certificate type, which is a higher level of
        # verification offered by edX.  This type of verification is useful for professional education/certifications
        certificate_type_description = _("A {cert_type} certificate signifies that a "
                                         "learner has agreed to abide by the honor code established by {platform_name} "
                                         "and has completed all of the required tasks for this course under its "
                                         "guidelines. A {cert_type} certificate also indicates that the "
                                         "identity of the learner has been checked and "
                                         "is valid.").format(cert_type=certificate_type,
                                                             platform_name=platform_name)
    elif mode == 'xseries':
        # Translators:  This text describes the 'XSeries' course certificate type.  An XSeries is a collection of
        # courses related to each other in a meaningful way, such as a specific topic or theme, or even an organization
        certificate_type_description = _("An {cert_type} certificate demonstrates a high level of "
                                         "achievement in a program of study, and includes verification of "
                                         "the student's identity.").format(cert_type=certificate_type)
    return certificate_type_description


def _update_certificate_context(context, course, user_certificate, platform_name):
    """
    Build up the certificate web view context using the provided values
    (Helper method to keep the view clean)
    """
    # Populate dynamic output values using the course/certificate data loaded above
    certificate_type = context.get('certificate_type')

    try:
        context['user_first_name'] = user_certificate.user.first_name
        context['user_last_name'] = user_certificate.user.last_name
    except User.DoesNotExist:
        context['user_first_name'] = 'Ivan'
        context['user_last_name'] = 'Ivanov'

    context['user_full_name'] = context['user_first_name'] + ' ' + context['user_last_name']

    context['grade'] = "{0:.0f}".format(float(user_certificate.grade) * 100)
    context['grade_percentage'] = "{0:.0f}%".format(float(user_certificate.grade) * 100)
    context['course_title'] = course.display_name

    # Override the defaults with any mode-specific static values
    context['certificate_id_number'] = user_certificate.verify_uuid
    context['cert_number'] = user_certificate.verify_uuid

    cert_number_short = binascii.crc32(str(user_certificate.verify_uuid))
    if cert_number_short < 0:
        cert_number_short = (-1) * cert_number_short
    context['cert_number_short'] = str(cert_number_short)
    context['certificate_verify_url'] = "{prefix}{uuid}{suffix}".format(
        prefix=context.get('certificate_verify_url_prefix'),
        uuid=user_certificate.verify_uuid,
        suffix=context.get('certificate_verify_url_suffix')
    )

    # Translators:  The format of the date includes the full name of the month
    date = display_date_for_certificate(course, user_certificate)
    context['certificate_date_issued'] = _('{month} {day}, {year}').format(
        month=strftime_localized(date, "%B"),
        day=date.day,
        year=date.year
    )
    context['cert_date'] = '{day}.{month}.{year}'.format(
        day=date.strftime('%d'),
        month=date.strftime('%m'),
        year=date.year
    )

    # Translators:  This text represents the verification of the certificate
    context['document_meta_description'] = _('This is a valid {platform_name} certificate for {user_name}, '
                                             'who participated in {partner_short_name} {course_number}').format(
        platform_name=platform_name,
        user_name=context['accomplishment_copy_name'],
        partner_short_name=context['organization_short_name'],
        course_number=context['course_number']
    )

    # Translators:  This text is bound to the HTML 'title' element of the page and appears in the browser title bar
    context['document_title'] = _("{partner_short_name} {course_number} Certificate | {platform_name}").format(
        partner_short_name=context['organization_short_name'],
        course_number=context['course_number'],
        platform_name=platform_name
    )

    # Translators:  This text fragment appears after the student's name (displayed in a large font) on the certificate
    # screen.  The text describes the accomplishment represented by the certificate information displayed to the user
    context['accomplishment_copy_description_full'] = _("successfully completed, received a passing grade, and was "
                                                        "awarded this {platform_name} {certificate_type} "
                                                        "Certificate of Completion in ").format(
        platform_name=platform_name,
        certificate_type=context.get("certificate_type"))

    certificate_type_description = get_certificate_description(user_certificate.mode, certificate_type, platform_name)
    if certificate_type_description:
        context['certificate_type_description'] = certificate_type_description

    # Translators: This text describes the purpose (and therefore, value) of a course certificate
    context['certificate_info_description'] = _("{platform_name} acknowledges achievements through "
                                                "certificates, which are awarded for course activities "
                                                "that {platform_name} students complete.").format(
        platform_name=platform_name,
        tos_url=context.get('company_tos_url'),
        verified_cert_url=context.get('company_verified_certificate_url'))


def _update_badge_context(context, course, user):
    """
    Updates context with badge info.
    """
    badge = None
    if badges_enabled() and course.issue_badges:
        badges = get_completion_badge(course.location.course_key, user).get_for_user(user)
        if badges:
            badge = badges[0]
    context['badge'] = badge


def _update_configuration_context(context, configuration):
    """
    Site Configuration will need to be able to override any hard coded
    content that was put into the context in the
    _update_certificate_context() call above. For example the
    'company_about_description' talks about edX, which we most likely
    do not want to keep in configurations.
    So we need to re-apply any configuration/content that
    we are sourcing from the database. This is somewhat duplicative of
    the code at the beginning of this method, but we
    need the configuration at the top as some error code paths
    require that to be set up early on in the pipeline
    """

    config_key = configuration_helpers.get_value('domain_prefix')
    config = configuration.get("microsites", {})
    if config_key and config:
        context.update(config.get(config_key, {}))


def _track_certificate_events(request, context, course, user, user_certificate):
    """
    Tracks web certificate view related events.
    """
    # Badge Request Event Tracking Logic
    course_key = course.location.course_key

    if 'evidence_visit' in request.GET:
        badge_class = get_completion_badge(course_key, user)
        if not badge_class:
            log.warning('Visit to evidence URL for badge, but badges not configured for course "%s"', course_key)
            badges = []
        else:
            badges = badge_class.get_for_user(user)
        if badges:
            # There should only ever be one of these.
            badge = badges[0]
            tracker.emit(
                'edx.badge.assertion.evidence_visited',
                {
                    'badge_name': badge.badge_class.display_name,
                    'badge_slug': badge.badge_class.slug,
                    'badge_generator': badge.backend,
                    'issuing_component': badge.badge_class.issuing_component,
                    'user_id': user.id,
                    'course_id': unicode(course_key),
                    'enrollment_mode': badge.badge_class.mode,
                    'assertion_id': badge.id,
                    'assertion_image_url': badge.image_url,
                    'assertion_json_url': badge.assertion_url,
                    'issuer': badge.data.get('issuer'),
                }
            )
        else:
            log.warn(
                "Could not find badge for %s on course %s.",
                user.id,
                course_key,
            )

    # track certificate evidence_visited event for analytics when certificate_user and accessing_user are different
    if request.user and request.user.id != user.id:
        emit_certificate_event('evidence_visited', user, unicode(course.id), course, {
            'certificate_id': user_certificate.verify_uuid,
            'enrollment_mode': user_certificate.mode,
            'social_network': CertificateSocialNetworks.linkedin
        })


def _render_valid_certificate(request, context, custom_template=None):
    if custom_template:
        template = Template(
            custom_template.template,
            output_encoding='utf-8',
            input_encoding='utf-8',
            default_filters=['decode.utf8'],
            encoding_errors='replace',
        )
        context = RequestContext(request, context)
        return HttpResponse(template.render(context))
    else:
        return render_to_response("certificates/valid.html", context)


def create_pdf_for_certificate(cert):
    fake_request = FakeRequest(cert.user)
    resp = render_html(fake_request, cert.user.id, str(cert.course_id))

    tmp_html = str(uuid4()) + '.html'
    tmp_html_path = os.path.join(tempfile.gettempdir(), tmp_html)
    tmp_html_file = open(tmp_html_path, 'w')
    tmp_html_file.write(resp.content)
    tmp_html_file.close()

    tmp_file1 = str(uuid4()) + '_1.pdf'
    tmp_file2 = str(uuid4()) + '_2.pdf'

    tmp_pdf_path1 = os.path.join(tempfile.gettempdir(), tmp_file1)
    tmp_pdf_path2 = os.path.join(tempfile.gettempdir(), tmp_file2)

    subprocess.call(
        settings.PDF_RENDER_BIN + ' --encoding UTF-8 -B 0 -L 0 -R 0 -T 0 ' + tmp_html_path + ' ' + tmp_pdf_path1,
        shell=True)

    if not os.path.isfile(tmp_pdf_path1):
        log.error("Can't create PDF file for user %d and course %s" % (cert.user.id, str(cert.course_id)))
        os.remove(tmp_html_path)
        return

    subprocess.call(
        'pdftk ' + tmp_pdf_path1 + ' cat 1 output ' + tmp_pdf_path2,
        shell=True)

    if not os.path.isfile(tmp_pdf_path2):
        log.error("Can't take first page from tmp PDF file for user %d and course %s"
                  % (cert.user.id, str(cert.course_id)))
        os.remove(tmp_pdf_path1)
        os.remove(tmp_html_path)
        return

    storage_class = settings.DEFAULT_FILE_STORAGE
    kwargs = {}
    if storage_class in ('storages.backends.s3boto.S3BotoStorage', 'openedx.core.storage.S3ReportStorage'):
        kwargs = {
            'bucket': settings.AWS_STORAGE_BUCKET_NAME,
            'location': 'certificates',
            'custom_domain': settings.AWS_S3_CUSTOM_DOMAIN
        }

    storage = get_storage(storage_class, **kwargs)
    storage_file_hash = str(uuid4()).replace('-', '')
    storage_certificate_file_path = str(cert.user.id) + '_' + storage_file_hash + '.pdf'

    if storage.exists(storage_certificate_file_path):
        storage.delete(storage_certificate_file_path)

    if cert.download_uuid:
        old_certificate_file_path = str(cert.user.id) + '_' + str(cert.download_uuid) + '.pdf'
        if storage.exists(old_certificate_file_path):
            storage.delete(old_certificate_file_path)

    with open(tmp_pdf_path2, 'r') as pdf_file:
        storage.save(storage_certificate_file_path, pdf_file)

    url_to_save = storage.url(storage_certificate_file_path)

    cert.download_url = url_to_save
    cert.download_uuid = storage_file_hash
    cert.save()

    os.remove(tmp_pdf_path2)
    os.remove(tmp_pdf_path1)
    os.remove(tmp_html_path)


def render_html(request, user_id, course_id):
    try:
        user_id = int(user_id)
    except ValueError:
        raise Http404

    preview_mode = request.GET.get('preview', None)
    platform_name = configuration_helpers.get_value("platform_name", settings.PLATFORM_NAME)
    configuration = CertificateHtmlViewConfiguration.get_config()

    # Kick the user back to the "Invalid" screen if the feature is disabled globally
    if not settings.FEATURES.get('CERTIFICATES_HTML_VIEW', False):
        return _render_invalid_certificate(course_id, platform_name, configuration)

    # Load the course and user objects
    try:
        course_key = CourseKey.from_string(course_id)
        user = User.objects.get(id=user_id)
        course = get_course_by_id(course_key)

    # For any course or user exceptions, kick the user back to the "Invalid" screen
    except (InvalidKeyError, User.DoesNotExist, Http404) as exception:
        error_str = (
            "Invalid cert: error finding course %s or user with id "
            "%d. Specific error: %s"
        )
        log.info(error_str, course_id, user_id, str(exception))
        return _render_invalid_certificate(course_id, platform_name, configuration)

    # Kick the user back to the "Invalid" screen if the feature is disabled for the course
    if not course.cert_html_view_enabled:
        log.info(
            "Invalid cert: HTML certificates disabled for %s. User id: %d",
            course_id,
            user_id,
        )
        return _render_invalid_certificate(course_id, platform_name, configuration)

    # Load user's certificate
    user_certificate = _get_user_certificate(request, user, course_key, course, preview_mode)
    if not user_certificate:
        log.info(
            "Invalid cert: User %d does not have eligible cert for %s.",
            user_id,
            course_id,
        )
        return _render_invalid_certificate(course_id, platform_name, configuration)

    # Get the active certificate configuration for this course
    # If we do not have an active certificate, we'll need to send the user to the "Invalid" screen
    # Passing in the 'preview' parameter, if specified, will return a configuration, if defined
    active_configuration = get_active_web_certificate(course, preview_mode)
    if active_configuration is None:
        log.info(
            "Invalid cert: course %s does not have an active configuration. User id: %d",
            course_id,
            user_id,
        )
        return _render_invalid_certificate(course_id, platform_name, configuration)

    # Get data from Discovery service that will be necessary for rendering this Certificate.
    catalog_data = _get_catalog_data_for_course(course_key)

    # Determine whether to use the standard or custom template to render the certificate.
    custom_template = None
    custom_template_language = None
    if settings.FEATURES.get('CUSTOM_CERTIFICATE_TEMPLATES_ENABLED', False):
        custom_template, custom_template_language = _get_custom_template_and_language(
            course.id,
            user_certificate.mode,
            catalog_data.pop('content_language', None)
        )

    # Determine the language that should be used to render the certificate.
    # For the standard certificate template, use the user language. For custom templates, use
    # the language associated with the template.
    user_language = translation.get_language()
    certificate_language = custom_template_language if custom_template else user_language

    # Generate the certificate context in the correct language, then render the template.
    with translation.override(certificate_language):
        context = {'user_language': user_language}

        _update_context_with_basic_info(context, course_id, platform_name, configuration)

        context['certificate_data'] = active_configuration

        # Append/Override the existing view context values with any mode-specific ConfigurationModel values
        context.update(configuration.get(user_certificate.mode, {}))

        # Append organization info
        _update_organization_context(context, course)

        # Append course info
        _update_course_context(request, context, course, course_key, platform_name)

        # Append course run info from discovery
        context.update(catalog_data)

        # Append user info
        _update_context_with_user_info(context, user, user_certificate)

        # Append social sharing info
        _update_social_context(request, context, course, user, user_certificate, platform_name)

        # Append/Override the existing view context values with certificate specific values
        _update_certificate_context(context, course, user_certificate, platform_name)

        # Append badge info
        _update_badge_context(context, course, user)

        # Append site configuration overrides
        _update_configuration_context(context, configuration)

        # Add certificate header/footer data to current context
        context.update(get_certificate_header_context(is_secure=request.is_secure()))
        context.update(get_certificate_footer_context())

        # Append/Override the existing view context values with any course-specific static values from Advanced Settings
        context.update(course.cert_html_view_overrides)

        # Track certificate view events
        _track_certificate_events(request, context, course, user, user_certificate)

        # Render the certificate
        return _render_valid_certificate(request, context, custom_template)
