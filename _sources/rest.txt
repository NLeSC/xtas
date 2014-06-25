REST API
========

When run as a webserver, xtas exposes a simple REST API to its tasks
(the one described in the :ref:`api`).
To tokenize a string using this API, you need to make two HTTP requests,
one to start a task and one to wait until it has completed.
Assuming default settings for the webserver, you can try::

    $ curl -H "Content-type: text/plain" -X POST -d 'Hello, world!' \
        http://127.0.0.1:5000/run/tokenize
    11d0f158-abdb-4a0a-860d-b365456122f4

The last line shows an id for the job that you submitted.
Since tokenization is very fast, you can immediately query the REST endpoint
again to get the results from the tokenization::

    $ curl http://127.0.0.1:5000/result/11d0f158-abdb-4a0a-860d-b365456122f4
    ["Hello", ",", "world", "!"]

Passing arguments to the task is also possible. To do so, you have to send the
API request as JSON, as follows::

    $ curl -H "Content-type: application/json" -X POST -d \
        '{"data": "Hello, world!", "arguments": {"output": "rank"}}'

The REST API, and this documentation, are very much in development.
