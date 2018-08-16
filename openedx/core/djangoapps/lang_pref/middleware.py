"""
Middleware for Language Preferences
"""

from django.conf import settings
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.utils.translation.trans_real import parse_accept_lang_header

from openedx.core.djangoapps.lang_pref import COOKIE_DURATION, LANGUAGE_HEADER, LANGUAGE_KEY
from openedx.core.djangoapps.user_api.errors import UserAPIInternalError, UserAPIRequestError
from openedx.core.djangoapps.user_api.preferences.api import (
    delete_user_preference,
    get_user_preference,
    set_user_preference
)
from xmodule.modulestore.django import modulestore
from util.request import course_id_from_url


class LanguagePreferenceMiddleware(object):
    """
    Middleware for user preferences.

    Ensures that, once set, a user's preferences are reflected in the page
    whenever they are logged in.
    """
    def process_request(self, request):
        if settings.FEATURES.get('USE_LANGUAGE_FROM_COURSE_SETTINGS', False) and 'lms' in settings.ROOT_URLCONF:
            self._update_lang_from_course_settings(request)
        else:
            self._process_request(request)

    def _process_request(self, request):
        """
        If a user's UserPreference contains a language preference, use the user's preference.
        Save the current language preference cookie as the user's preferred language.
        """
        cookie_lang = request.COOKIES.get(settings.LANGUAGE_COOKIE, None)
        if cookie_lang:
            if request.user.is_authenticated():
                set_user_preference(request.user, LANGUAGE_KEY, cookie_lang)
            else:
                request._anonymous_user_cookie_lang = cookie_lang

            accept_header = request.META.get(LANGUAGE_HEADER, None)
            if accept_header:
                current_langs = parse_accept_lang_header(accept_header)
                # Promote the cookie_lang over any language currently in the accept header
                current_langs = [(lang, qvalue) for (lang, qvalue) in current_langs if lang != cookie_lang]
                current_langs.insert(0, (cookie_lang, 1))
                accept_header = ",".join("{};q={}".format(lang, qvalue) for (lang, qvalue) in current_langs)
            else:
                accept_header = cookie_lang
            request.META[LANGUAGE_HEADER] = accept_header

            # Allow the new cookie setting to update the language in the user's session
            if LANGUAGE_SESSION_KEY in request.session and request.session[LANGUAGE_SESSION_KEY] != cookie_lang:
                del request.session[LANGUAGE_SESSION_KEY]

    def process_response(self, request, response):
        if settings.FEATURES.get('USE_LANGUAGE_FROM_COURSE_SETTINGS', False) and 'lms' in settings.ROOT_URLCONF:
            return response

        # If the user is logged in, check for their language preference
        if getattr(request, 'user', None) and request.user.is_authenticated():
            user_pref = None

            anonymous_cookie_lang = getattr(request, '_anonymous_user_cookie_lang', None)
            if anonymous_cookie_lang:
                user_pref = anonymous_cookie_lang
                set_user_preference(request.user, LANGUAGE_KEY, anonymous_cookie_lang)
            else:
                # Get the user's language preference
                try:
                    user_pref = get_user_preference(request.user, LANGUAGE_KEY)
                except (UserAPIRequestError, UserAPIInternalError):
                    # If we can't find the user preferences, then don't modify the cookie
                    pass

            # If set, set the user_pref in the LANGUAGE_COOKIE
            if user_pref:
                response.set_cookie(
                    settings.LANGUAGE_COOKIE,
                    value=user_pref,
                    domain=settings.SESSION_COOKIE_DOMAIN,
                    max_age=COOKIE_DURATION,
                )
            else:
                response.delete_cookie(
                    settings.LANGUAGE_COOKIE,
                    domain=settings.SESSION_COOKIE_DOMAIN
                )

        return response

    def _update_lang_from_course_settings(self, request):
        course_key = course_id_from_url(request.path)
        if course_key:
            course = modulestore().get_course(course_key)
            if course and hasattr(course, 'language') and course.language:
                request.session[LANGUAGE_SESSION_KEY] = course.language
                return True
        return False
