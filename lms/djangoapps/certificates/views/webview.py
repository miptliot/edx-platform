# pylint: disable=bad-continuation
"""
Certificate HTML webview.
"""
import logging
from django.http import Http404
from django.utils import translation
from lms.djangoapps.certificates.api import (
    render_html
)
from lms.djangoapps.certificates.models import (
    CertificateStatuses,
    GeneratedCertificate
)
from util.views import handle_500


log = logging.getLogger(__name__)
_ = translation.ugettext


def render_cert_by_uuid(request, certificate_uuid):
    """
    This public view generates an HTML representation of the specified certificate
    """
    try:
        certificate = GeneratedCertificate.eligible_certificates.get(
            verify_uuid=certificate_uuid,
            status=CertificateStatuses.downloadable
        )
        return render_html_view(request, certificate.user.id, unicode(certificate.course_id))
    except GeneratedCertificate.DoesNotExist:
        raise Http404


@handle_500(
    template_path="certificates/server-error.html",
    test_func=lambda request: request.GET.get('preview', None)
)
def render_html_view(request, user_id, course_id):
    """
    This public view generates an HTML representation of the specified user and course
    If a certificate is not available, we display a "Sorry!" screen instead
    """
    return render_html(request, user_id, course_id)
