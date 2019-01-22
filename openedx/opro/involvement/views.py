from django.http import Http404, HttpResponseRedirect
from django.views.decorators.http import require_GET

from openedx.opro.involvement.models import UserCourseInvolvement


@require_GET
def change_involvement_status(request):
    user = request.user
    if not user:
        return Http404
    if UserCourseInvolvement.objects.filter(user=user, is_active=True).exists():
        UserCourseInvolvement.objects.filter(user=user).update(is_active=False)
    elif UserCourseInvolvement.objects.filter(user=user, is_active=False).exists():
        UserCourseInvolvement.objects.filter(user=user).update(is_active=True)
    else:
        UserCourseInvolvement.objects.create(user=user, is_active=True)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
