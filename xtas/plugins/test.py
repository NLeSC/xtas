"""Simple tasks for testing and debugging."""

from time import sleep

from ..taskregistry import task


@task(takes=None)
def trivial_task(config):
    sleep(5)
    return "success"
