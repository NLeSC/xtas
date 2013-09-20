"""Task that always succeeds, for testing and debugging."""

from ..taskregistry import task


@task('/test')
def test_task():
    return "success"
