"""Task that always fails, for testing and debugging."""

from ..taskregistry import task


@task('/fail')
def fail():
    raise ValueError("foo")
