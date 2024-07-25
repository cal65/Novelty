# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery_tasks import app as celery_app

import goodreads.dash_list
__all__ = ("celery_app",)
