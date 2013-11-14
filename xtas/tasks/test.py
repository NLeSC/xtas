"""Simple tasks for testing and debugging."""

from ..taskregistry import task


@task('/test')
def trivial_task(config):
    return "success"
