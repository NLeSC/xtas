# Default configuration for Celery; can be overridden with an
# xtas_celeryconfig module in the PYTHONPATH.

BROKER_URL = 'amqp://'
CELERY_RESULT_BACKEND = 'amqp://'

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'Europe/Amsterdam'
CELERY_ENABLE_UTC = True

CELERY_TASK_RESULT_EXPIRES = 3600

# Uncomment the following to make Celery tasks run locally (for debugging).
#CELERY_ALWAYS_EAGER = True
