"""
Middleware for Language Preferences
"""
from django.conf import settings
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.utils.translation.trans_real import parse_accept_lang_header

from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.lang_pref.api import released_languages
from openedx.core.djangoapps.user_api.preferences.api import get_user_preference, delete_user_preference
from xmodule.modulestore.django import modulestore
from util.request import course_id_from_url


class LanguagePreferenceMiddleware(object):
    """
    Middleware for user preferences.

    Ensures that, once set, a user's preferences are reflected in the page
    whenever they are logged in.
    """

    def process_request(self, request):
        """
        If a user's UserPreference contains a language preference, use the user's preference.
        """
        languages = released_languages()
        system_released_languages = [seq[0] for seq in languages]

        # If the user is logged in, check for their language preference
        if request.user.is_authenticated():

            if settings.FEATURES.get('USE_LANGUAGE_FROM_COURSE_SETTINGS', False) and 'lms' in settings.ROOT_URLCONF:
                self._update_lang_from_course_settings(request)
            else:
                # Get the user's language preference
                user_pref = get_user_preference(request.user, LANGUAGE_KEY)
                # Set it to the LANGUAGE_SESSION_KEY (Django-specific session setting governing language pref)
                if user_pref:
                    if user_pref in system_released_languages:
                        request.session[LANGUAGE_SESSION_KEY] = user_pref
                    else:
                        delete_user_preference(request.user, LANGUAGE_KEY)

    def _update_lang_from_course_settings(self, request):
        course_key = course_id_from_url(request.path)
        if course_key:
            course = modulestore().get_course(course_key)
            if course and hasattr(course, 'language') and course.language:
                request.session[LANGUAGE_SESSION_KEY] = course.language
                return True
        return False
