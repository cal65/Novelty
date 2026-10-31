from django.apps import AppConfig


class GoodreadsConfig(AppConfig):
    name = "goodreads"

    def ready(self):
        # django-plotly-dash uses request.session[key] which raises KeyError when the
        # session key is missing (e.g. stale URL, crawl bot, expired session). Patch it
        # to use .get() so _dash-layout doesn't crash with a 500.
        import django_plotly_dash.util as dpd_util

        def _safe_get_initial_arguments(request, cache_id=None):
            if cache_id is None:
                return None
            if dpd_util.initial_argument_location():
                return dpd_util.cache.get(cache_id)
            return request.session.get(cache_id)

        dpd_util.get_initial_arguments = _safe_get_initial_arguments
