"""Basic test module."""

from xiao_flasher import __version__


def test_version() -> None:
    """Test package version string."""
    assert __version__ == "1.0.0"
