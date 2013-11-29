from __future__ import absolute_import

from celery import Celery

app = Celery('proj', include=['xtas.tasks'])
app.config_from_object('celeryconfig')

# Optional configuration, see the application user guide.
app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)

if __name__ == '__main__':
    app.start()
