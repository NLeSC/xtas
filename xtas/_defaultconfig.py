# Copyright 2013-2015 Netherlands eScience Center and University of Amsterdam
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Default configuration for xtas.
# Can be overridden by an xtas_config module in the PYTHONPATH, with the same
# general structure as this module.

# See http://docs.celeryproject.org/en/latest/configuration.html for the
# allowed options in this dict.
CELERY = dict(
    BROKER_URL='amqp://',
    CELERY_RESULT_BACKEND='amqp://',

    CELERY_TASK_SERIALIZER='json',
    CELERY_RESULT_SERIALIZER='json',
    CELERY_ACCEPT_CONTENT=['json'],
    CELERY_TIMEZONE='Europe/Amsterdam',
    CELERY_ENABLE_UTC=True,

    CELERY_TASK_RESULT_EXPIRES=3600,

    # Uncomment the following to make Celery tasks run locally (for debugging).
    #CELERY_ALWAYS_EAGER=True,
)

# See https://elasticsearch-py.readthedocs.org/en/latest/api.html#elasticsearch.Elasticsearch
# for the allowed options.
ELASTICSEARCH = [
    {"host": "localhost", "port": 9200},
    # add more hosts here
]

# Additional modules to load in the worker and webserver.
EXTRA_MODULES = [
]
